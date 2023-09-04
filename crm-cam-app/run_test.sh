#!/bin/bash

CURPATH=$(cd `dirname $0` && pwd)
export MTKEXPR='MICROENV=test PORTBASE=21400 DEBUGMODE=1 LOGLEVEL=DEBUG' && $CURPATH/run_prod.sh $@
