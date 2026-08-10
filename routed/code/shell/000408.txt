# Job configuration file

# Timestamp format
TS="date +%Y-%m-%d-%H:%M:%S"

JOBS_DIR="~/jobs"
JOBS_LOG_DIR="$JOBS_DIR/logs"

# Do not attempt to restart server if this file is present
MAINTENANCE_FILE="$JOBS_DIR/.LOCKFILE"

# arma 3 base directory
A3_DIR="~/serverfiles"
# Where missions are stored
MISSIONS_FOLDER="$A3_DIR/mpmissions"
# Where old missions are moved
OLD_MISSIONS_FOLDER="~/old-mpmissions"
# Maximum number of days missions permitted to stay in mpmissions folder
MISSION_MAX_AGE_DAYS=30
# Do not move this mission if filename matches this regex
MISSION_KEEP_REGEX="*.pbo"


function server_stop(name){
	echo "${TS} - Stopping server: $name"
	`~./$name stop`
}

function server_start(server){
	echo "${TS} - Starting server: $name"
	if [ ! -f "$MAINTENANCE_FILE" ]; then
		`~./$name force-update`
		`~./$name start`
	else
		echo "${TS} - Cannot start server - Maintenance flag found: $name"
	fi
}
