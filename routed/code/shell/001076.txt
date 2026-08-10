#!/bin/bash
set -x
exec > /tmp/master.log 2>&1

sudo emrfs create-metadata -r 50 -w 10

export AWS_DEFAULT_REGION=eu-west-1

sleep 120
echo "Launch StepFunction"
aws stepfunctions start-execution --state-machine-arn arn:aws:states:eu-west-1:323361102328:stateMachine:devfest --input '{"message": {"message": "DevFest Issue"}}'

