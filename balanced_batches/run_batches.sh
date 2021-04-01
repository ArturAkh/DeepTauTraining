#!/bin/bash

source /cvmfs/sft.cern.ch/lcg/views/LCG_99/x86_64-centos7-gcc10-opt/setup.sh

JOBCONFIG=${1}
JOBID=$(basename ${JOBCONFIG})
JOBID=${JOBID/job_/}
JOBID=${JOBID/.json/}

echo "Performing job with configuration ${JOBCONFIG} with job ID ${JOBID}"

python make_batches.py ${JOBCONFIG}

echo "Merging outputs together"

hadd batch${JOBID}.root *_batch${JOBID}.root
