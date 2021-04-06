#!/bin/bash

JOBCONFIG=${1}
JOBID=$(basename ${JOBCONFIG})
JOBID=${JOBID/job_/}
JOBID=${JOBID/.json/}
OUTPUT=batch${JOBID}.root

source additional_environment.sh

echo "Performing job with configuration ${JOBCONFIG} with job ID ${JOBID}" $(date +"%Y-%M-%d %H:%M:%S.%6N")

./run_batches.sh ${JOBCONFIG} ${JOBID}

echo "Copying output" $(date +"%Y-%M-%d %H:%M:%S.%6N")
echo "Destination: ${BALANCED_BATCHES_OUTPUTDIR}"

./copy_batches.sh ${OUTPUT} ${BALANCED_BATCHES_OUTPUTDIR}

echo "Job finished" $(date +"%Y-%M-%d %H:%M:%S.%6N")
