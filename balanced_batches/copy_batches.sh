#!/bin/bash

OUTPUT=${1}
DESTINATION=${2}

source /cvmfs/grid.cern.ch/umd-c7ui-latest/etc/profile.d/setup-c7-ui-example.sh

gfal-copy --parent --force --abort-on-failure ${OUTPUT} ${DESTINATION}/${OUTPUT}
