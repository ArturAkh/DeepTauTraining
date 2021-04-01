#!/bin/bash

JOBCONFIG=${1}
JOBID=$(basename ${JOBCONFIG})
JOBID=${JOBID/job_/}
JOBID=${JOBID/.json/}
OUTPUT=batch${JOBID}.root

source additional_environment.sh

echo "Performing job with configuration ${JOBCONFIG} with job ID ${JOBID}"

./run_batches.sh ${JOBCONFIG} ${JOBID}

echo "Copying output ${OUTPUT} to destination ${BALANCED_BATCHES_OUTPUTDIR} (overwriting enabled)"

./copy_batches.sh ${OUTPUT} ${BALANCED_BATCHES_OUTPUTDIR}
