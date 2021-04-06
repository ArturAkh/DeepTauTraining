#!/bin/bash

source /cvmfs/sft.cern.ch/lcg/views/LCG_99/x86_64-centos7-gcc10-opt/setup.sh

JOBCONFIG=${1}
JOBID=$(basename ${JOBCONFIG})
JOBID=${JOBID/job_/}
JOBID=${JOBID/.json/}

python make_batches.py ${JOBCONFIG}

echo "Merging outputs together" $(date +"%Y-%M-%d %H:%M:%S.%6N")

hadd -f batch${JOBID}.root *_batch${JOBID}.root
