#!/bin/bash

# === 1. Customize Arguments (DO CHANGES) ===

#module of sub class of Processor()
PROCCLS=topic_data_process.TaskProc

#environ key: debug|trial|micro
MICROENV=$(test -n "$MTK_ENV_VAR" && echo "$MTK_ENV_VAR" || echo "prod")
#concurrent workers, greater than 0
WORKERS=1

#DEBUG|INFO|WARNING|ERROR|NONE
LOGLEVEL=INFO

#debug mode of sanic framework, can be: [0,1]
DEBUGMODE=0

#extra path for importing, can be empty
INCLUDEDIR=

#count of default access log
LOGCOUNT=90

# === 2. Initialize Variables (DO NOT CHANGE) ===
MKTDIR=$(cat "$HOME/.path_microkit" 2>/dev/null)
if [ ! -d "$MKTDIR" ]; then
  echo "Missing or Invalid .path_microkit!"
  echo "Should enter into MTK and run setup.sh"
  exit 2
fi
source $MKTDIR/start-proc.source
