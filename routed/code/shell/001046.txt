#!/usr/bin/env bash

# Description
# -----------
#    Simple wrapper to for terraform to deploy infrastructure into different
#    AWS accounts (environments) using two shared AWS S3 backends, one for 
#    productions deployments and another for non-production.
#    (Note: the Terraform S3 backends must be previously configured)

# Workflow/Steps Overview
# ----------------------
#    1. parse/verify command line arguements and settings
#    2. select the appropiate terraform backend configuration file
#    3. initialize the terraform backend with `terraform init`
#       a. generate the AWS S3 bucket key value dynamically from command line
#          options given and the project setting in the *.tfvars file
#       b. determine which backend config file to use depending on whether or
#          not the environment to deploy is prod or non-prod
#       c. invoke `terraform init` with '-backend-config' options to specify
#          both the appropiate backend conig file and S3 key setting
#    4. validate the terraform configuration(s) with `terraform init`
#    5. run a desired terraform COMMAND (if applicable - i.e. the user
#       specified a terraform command to run, otherwise enter maintenance mode)

# Terminology: AWS resources and Terraform configs
# ------------------------------------------------
#    common: (EC2 security groups and Terraform variables) [file names]
#       used by all resources (EC2 and TF configs)
#
#    shared: (AWS resources) [deploy setting]
#       resources used by few/specific resources (DB's, ES, RabbitMQ, KMS,
#       SG's, Etc.) (only specified/significant when deploying to `pie` and
#       `prod`, and you'll only see that "shared" designation when deployed to
#       `pie` and `prod` in the names of the TF state files and the names of
#       the AWS resources)
#
#    global: (region)        [region setting]
#       refers to whether or not the AWS resource is region specific
#       (IAM|R53|WAF|CloudFront - no, EC2|S3|VPC|etc. - yes)

# Debug/Investigation/Maintenance Mode
# ------------------------------------
#    If a Terraform command (e.g. plan or apply) is not given, this script will
#    initialize the appropiate S3 backend configuration (S3 bucket & key) and
#    then change the working directory to the module desired to maintain, then
#    start a shell to allow the user to perform Terraform debugging,
#    investigation and maintenance commands (e.g. show and import).
#    The user will see a prompt showing the:
#       1. S3 backend configuration state file details (S3 bucket/key)
#       2. current working directory (highlight the fact that they are now
#          in the directory of the module to be worked on
#       3. "TF DEBUG" prompt
#    At this point one can run, e.g.:
#       - terraform show    # read and output the Terraform state file
#       - terraform import  # import existing infrastructure into the state file
#    To exit this mode, simply type 'exit' and hit [return]


# Global Settings/Variables
# set -x   # enable "debug" mode
set -e     # exit immediately if a simple command exits with a non-zero status
exec 3>&1  # create a link to STDOUT for terraform to output to
exec 1>&2  # send STDOUT to STDERR

readonly BACKEND_SSPD="sspd-backend.tfvars"   # backend config for prod
readonly BACKEND_SSNP="ssnp-backend.tfvars"   # backend config for non prod
readonly COMMON_DIR="common"                  # common directory of shared files
readonly DEFAULT_RESOURCE_REGION="us-west-2"  # default region for global deploy
readonly DEV_ENV="dv"                         # Valid development environment
readonly DEPLOY_ENVS="sg pd"                  # Envs that require DEPLOY val
readonly NON_PROD_ENVS="qa dv sg ssnp"        # Non "prod" environments
readonly PROD_ENVS="pd sspd"                  # "prod" environments
readonly THIS_SCRIPT=$(basename $0)           # name of the script invoked
readonly VALID_DEPLOYS="blue green shared"    # Valid options for DEPLOY value

# for coloring the bash prompt when entering maintenance mode
PGRN='\[\e[1;32m\]'  # green (bold)
PBLU='\[\e[1;34m\]'  # blue (bold)
PCYN='\[\e[1;36m\]'  # cyan (bold)
PNRM='\[\e[m\]'      # normal

# Usage
readonly USAGE="\
usage: $THIS_SCRIPT [options]
required options:
  -e | --env ENV        Environment to deploy
                        (non-prod: $NON_PROD_ENVS)
                        (prod: $PROD_ENVS)
  -m | --module MODULE  Module (service) to deploy
                        (e.g. aws-iam-roles, cryt-tier, etc.)
  -r | --region REGION  AWS region to deploy
                        (e.g. global, us-west-2, us-east-1, etc.)
conditional options:
  -d | --deploy DEPLOY  Deployment to launch ($VALID_DEPLOYS)
                        (required for environments: $DEPLOY_ENVS)
  -v | --vars VARS_SETTINGS_FILE
                        Variable settings file to use
                        only available for $DEV_ENV environment
                        (default: MODULE/ENV.tfvars)
optional options:
  --debug               Turn on debugging
  -h | --help           Show usage/help (this message)"


function usage () {
   local _msg=$1
   local _err=$2
   [ "$debug" == "true" ] && show_debug_info  # display variables/settings
   [ -n "$_msg" ] && echo -e "$_msg"
   echo "$USAGE"
   [ -n "$_err" ] && exit $_err || exit 1
}


function parse_args () {
# parse command line arguments

   debug="false"
   while [ $# -gt 0 ]; do
      case $1 in
         -d|--deploy) DEPLOY="$2"    ; shift 2;;
         --debug)     debug="true"   ; shift 1;;
         -e|--env)    ENV="$2"       ; shift 2;;
         -h|--help)   usage "" 0     ; exit   ;;
         -m|--module) MODULE="$2"    ; shift 2;;
         -r|--region) REGION="$2"    ; shift 2;;
         -v|--vars)   VARS_FILE="$2" ; shift 2;;
         -*)          usage "error: unknown option: $1";;
         *)           TF_CMD="$@"    ; break  ;;
      esac
   done
   return 0
}


function run_sanity_checks () {
# perform basic sanity checks

   [ -z "$ENV" ] &&
      usage "error: missing required ENV option"
   [[ ! $PROD_ENVS =~ (^| )$ENV($| ) && ! $NON_PROD_ENVS =~ (^| )$ENV($| ) ]] &&
      usage "error: invalid environment: $ENV"
   [ -z "$MODULE" ] &&
      usage "error: missing required MODULE option"
   [ -z "$REGION" ] &&
      usage "error: missing required REGION option"
   [ ! -d "$MODULE" ] &&
      usage "error: module NOT found: $MODULE"
   [[ $DEPLOY_ENVS =~ (^| )$ENV($| ) && -z "$DEPLOY" ]] &&
      usage "error: DEPLOY required for environment: $ENV"
   [[ ! $DEPLOY_ENVS =~ (^| )$ENV($| ) && -n "$DEPLOY" ]] &&
      usage "error: DEPLOY option not applicable for environment: $ENV"
   [[ -n "$DEPLOY" && ! $VALID_DEPLOYS =~ (^| )$DEPLOY($| ) ]] && 
      usage "error: invalid DEPLOY option: $DEPLOY"
   if [ -n "$VARS_FILE" -a $ENV != "$DEV_ENV" ]; then
      usage "error: VARS_SETTINGS_FILE option only avail with environment: $DEV_ENV"
   else
      VARS_FILE="$MODULE/$ENV.tfvars"
   fi
   [ ! -e "$VARS_FILE" ] &&
      echo "error: tfvars file NOT found: $VARS_FILE" && exit 1
   return 0
}


function set_be_cfg_vars () {
# set default backend config variable settings

   [[ $PROD_ENVS =~ (^| )$ENV($| ) ]] && BACKEND_CFG="$COMMON_DIR/$BACKEND_SSPD"
   [[ $NON_PROD_ENVS =~ (^| )$ENV($| ) ]] && BACKEND_CFG="$COMMON_DIR/$BACKEND_SSNP"
   [ -z "$BACKEND_CFG" ] && {
      echo "error: backend config could NOT be set"; exit 1; }
   [ ! -e "$BACKEND_CFG" ] &&
      usage "error: backend config NOT found: $BACKEND_CFG"
   return 0
}


function get_module_settings () {
# get module settings from VARS_FILE

   # get and make sure project is defined in $VARS_FILE
   readonly PROJECT=$(
      grep '^project = ' $VARS_FILE | cut -d'"' -f2 | tr '[A-Z]' '[a-z]')
   [ -z "$PROJECT" ] && {
      echo "error: project not defined in: $VARS_FILE"; exit 1; }
   # check if deployment statically assigned (not blue or green)
   readonly STATIC_DEPLOY=$(
      grep '^deploy = ' $VARS_FILE | cut -d'"' -f2 | tr '[A-Z]' '[a-z]')
   [[ -n $STATIC_DEPLOY ]] && [[ ! $DEPLOY == $STATIC_DEPLOY ]] && {
      echo "error: this stack defines a static deployment of \"$STATIC_DEPLOY\"
      which does not match your argument of \"$DEPLOY\""; exit 1; }
   # check if region statically assigned
   readonly STATIC_REGION=$(
      grep '^region = ' $VARS_FILE | cut -d'"' -f2 | tr '[A-Z]' '[a-z]')
   [[ -n $STATIC_REGION ]] && [[ ! $REGION == $STATIC_REGION ]] && {
      echo "error: this stack defines a static region of \"$STATIC_REGION\"
      which does not match your argument of \"$REGION\""; exit 1; }
   return 0
}


function configure_tf_env_vars () {
# configure environment variables for use by module

   readonly TF_VAR_app=$PROJECT
   readonly TF_VAR_colorstack=${DEPLOY}
   readonly TF_VAR_deploy=${DEPLOY::1}
   readonly TF_VAR_env=$ENV
   readonly TF_VAR_environment=$(echo $ENV | tr '[a-z]' '[A-Z]')
   if [ "$REGION" == "global" ]; then
      readonly TF_VAR_region=$DEFAULT_RESOURCE_REGION
   else
      readonly TF_VAR_region=$REGION
   fi
   return 0
}


function show_debug_info () {
# display environment variables/settings for debugging purposes

   echo "
debug (variable settings):
   Backend Config File (BACKEND_CFG):      ${BACKEND_CFG:-N/A (Not Set)}
   Deploy (DEPLOY):                        ${DEPLOY:-N/A (Not Set)}
   Environment (ENV):                      ${ENV:-N/A (Not Set)}
   Module (MODULE):                        ${MODULE:-N/A (Not Set)}
   Project (PROJECT):                      ${PROJECT:-N/A (Not Set)}
   Region (REGION):                        ${REGION:-N/A (Not Set)}
   Static Deploy (STATIC_DEPLOY):          ${STATIC_DEPLOY:-N/A (Not Set)}
   Static Region (STATIC_REGION):          ${STATIC_REGION:-N/A (Not Set)}
   Terraform Command (TF_CMD):             ${TF_CMD:-N/A (Not Set)}
   Terraform Vars File (VARS_FILE):        ${VARS_FILE:-N/A (Not Set)}
   Terraform State File (STATE_FILE_NAME): ${STATE_FILE_NAME:-N/A (Not Set)}
   AWS S3 Bucket Key (S3_KEY):             ${S3_KEY:-N/A (Not Set)}
debug (terraform environment settings):
   Application (TF_VAR_app):               ${TF_VAR_app:-N/A (Not Set)}
   Colorstack (TF_VAR_colorstack):         ${TF_VAR_colorstack:-N/A (Not Set)}
   Deployment (TF_VAR_deploy):             ${TF_VAR_deploy:-N/A (Not Set)}
   Env (TF_VAR_env):                       ${TF_VAR_env:-N/A (Not Set)}
   Environment (TF_VAR_environment):       ${TF_VAR_environment:-N/A (Not Set)}
   Region (TF_VAR_region):                 ${TF_VAR_region:-N/A (Not Set)}
   "
   return 0
}


function initialize_tf_be () {
# initiatialize the terraform backend

# Backend AWS S3 Bucket Key naming format:
#   <env>/<region>/[<deploy>/]<state_file_name>.tfstate
# where:
#  <state_file_name> = <project>-<env>-<service>-[<color>-][<region>]
#  <region>          = AWS region (e.g. us-east-1, us-west-2, etc. or global)
#  <deploy>          = blue|green|shared
#  <color>           = b|g
# e.g. "sspd/us-west-2/shared/proj-sspd-tf-init-us-west-2.tfstate"

if [ "$REGION" == "global" ]; then
   STATE_FILE_NAME="$PROJECT-$ENV-${MODULE##*/}-$REGION.tfstate"
   S3_KEY="$ENV/$REGION/$STATE_FILE_NAME"
else
   STATE_FILE_NAME="$PROJECT-$ENV-${MODULE##*/}-${DEPLOY::1}${DEPLOY:+-}$REGION.tfstate"
   S3_KEY="$ENV/$REGION/$DEPLOY${DEPLOY:+/}$STATE_FILE_NAME"
fi
echo
echo "running: terraform init -reconfigure
   -backend-config $BACKEND_CFG
   -backend-config key=$S3_KEY
   $MODULE"
terraform init -reconfigure \
   -backend-config $BACKEND_CFG \
   -backend-config key=$S3_KEY \
   $MODULE
   return 0
}


function validate_tf_configs () {
   # validate terraform configuration(s)

   echo
   echo "running: terraform validate -var-file $VARS_FILE $MODULE"
   terraform validate -var-file $VARS_FILE $MODULE >&3
   [ $? -ne 0 ] && { echo "error: terraform validation failed"; exit; }
   return 0
}


function run_tf_command () {
# run terraform command (if applicable) or enter maintenance mode

   if [ -n "$TF_CMD" ]; then
      echo
      echo "running: terraform $TF_CMD -var-file $VARS_FILE $MODULE"
      terraform $TF_CMD -var-file $VARS_FILE $MODULE >&3
   else
      s3_bucket=$(grep "bucket *= " $BACKEND_CFG | cut -d'"' -f2)
      echo
      echo "opening new shell for testing (type 'exit' or ^D to quit)"
      echo "(for verbose output; export TF_LOG=TRACE)"
      echo "(for debug output; export TF_LOG=DEBUG)"
      unset PROMPT_COMMAND
      EXECED_WD=$(pwd)     # dir where the wrapper was execed from
      cd $MODULE           # cd to the "module" desired to be launched
      [ -e .terraform ] && mv .terraform{,.orig.$$}  # save current .terraform dir
      ln -s $EXECED_WD/.terraform  # set up symlink to backend initialized
      export PS1="\n${PCYN}(state file: s3://$s3_bucket/$S3_KEY)\n${PGRN}[path: \w]\n${PBLU}{TF DEBUG ('exit' to quit)}$ ${PNRM}"
      bash --noprofile --norc
      rm -f .terraform     # remove the symlink
      [ -e .terraform.orig.$$ ] && mv .terraform{.orig.$$,}  # restore original .terraform directory
      cd $EXECED_WD        # cd back to the original working directory
   fi
   return 0
}


# MAIN #

parse_args $*          # parse command line arguments
run_sanity_checks      # perform basic sanity checks
set_be_cfg_vars        # set default backend config variable settings
get_module_settings    # get module settings from VARS_FILE
configure_tf_env_vars  # configure environment variables for use by module
initialize_tf_be       # initiatialize the terraform backend
if [ "$debug" == "true" ]; then
   show_debug_info     # display environment variables/settings
   export TF_LOG=DEBUG
fi
validate_tf_configs    # validate terraform configuration(s)
run_tf_command         # run terraform command  or enter maintenance mode
