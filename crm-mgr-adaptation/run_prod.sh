#!/bin/bash

# === 1. Customize Arguments (DO CHANGES) ===
#module of app=Sanic(...)
SANICAPP=main.app

#environ key: local|test|prod
MICROENV=prod

#host (ip) for listening
LISTENHOST=0.0.0.0

#base listening port
PORTBASE=21300

#reuse port when greater than 1
WORKERS=1

#DEBUG|INFO|WARNING|ERROR|NONE
LOGLEVEL=INFO

#debug mode of sanic framework, can be: [0,1]
DEBUGMODE=0

#extra path for importing, can be empty
INCLUDEDIR=..

#flag of output access log
ACCESSLOG=1

#number of log backups
LOGCOUNT=60

#customization of loggers
#LOGMORE=conf/logger.py


# === 2. Initialize Variables (DO NOT CHANGE) ===
MKTDIR=$(cat "$HOME/.path_microkit" 2>/dev/null)
if [ ! -d "$MKTDIR" ]; then
  echo "Missing or Invalid .path_microkit!"
  echo "Should enter into MTK and run setup.sh"
  exit 2
fi
source $MKTDIR/run.source


