#!/bin/bash

CURPATH=$(cd `dirname $0` && pwd)
export MTKEXPR='MICROENV=local PORTBASE=21300 DEBUGMODE=1 LOGLEVEL=DEBUG' && $CURPATH/run_prod.sh $@
