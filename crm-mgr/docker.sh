#!/bin/bash

#environ key: prod|test|dev|local
MICROENV="prod"

# hostname of registry hub, can be empty
HUB_HOST=""

# name of registry hub
HUB_NAMESPACE="neocrm"

# project (app) name, can be empty
APP_NAME="crm-mgr"

# === 2. Initialize Variables (DO NOT CHANGE) ===
MKTDIR=$(cat "$HOME/.path_microkit" 2>/dev/null)
if [ ! -d "$MKTDIR" ]; then
  echo "Missing or Invalid .path_microkit!"
  echo "Should enter into MTK and run setup.sh"
  exit 2
fi

#export MTKEXPR='HUB_NAMESPACE=ocpecdevacr HUB_HOST=ocpecdevacr.azurecr.cn APP_NAME=ec-be-mgr' &&  $MKTDIR/run.source build-docker
source $MKTDIR/run.source build-docker
