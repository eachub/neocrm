#!/bin/bash

# === 1. Customize Arguments (DO CHANGES) ===

#module of sub class of Processor()
PROCCLS=crm_coupon_code_gen_proc.CrmCouponCodeGenProc

#environ key: debug|trial|micro
MICROENV=prod

#concurrent workers, greater than 0
WORKERS=1

#DEBUG|INFO|WARNING|ERROR|NONE
LOGLEVEL=INFO

#debug mode of sanic framework, can be: [0,1]
DEBUGMODE=0

#extra path for importing, can be empty
INCLUDEDIR=..

#count of default access log
LOGCOUNT=30

# === 2. Initialize Variables (DO NOT CHANGE) ===
MKTDIR=$(cat "$HOME/.path_microkit" 2>/dev/null)
if [ ! -d "$MKTDIR" ]; then
  echo "Missing or Invalid .path_microkit!"
  echo "Should enter into MTK and run setup.sh"
  exit 2
fi
source $MKTDIR/start-proc.source
