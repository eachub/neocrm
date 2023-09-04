#!/bin/bash

CURPATH=$(cd `dirname $0` && pwd)
export MTKEXPR='MICROENV=local PORTBASE=21200 DEBUGMODE=1 LOGLEVEL=DEBUG' && $CURPATH/run_prod.sh $@
