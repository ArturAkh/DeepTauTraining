#!/bin/bash

source /cvmfs/sft.cern.ch/lcg/views/LCG_98a/x86_64-centos7-gcc10-opt/setup.sh

JOBID=${1}
BATCHSIZE=${2}
SELECTIONS=${3}
STORAGE=${4}

echo "Performing job ${JOBID} with selections ${SELECTIONS} and batchsize ${BATCHSIZE}"

python make_batches.py \
    --filelist filelist.txt \
    --ptabsetabins binning.yaml \
    --countinfo summed_info.json \
    --job ${JOBID} \
    --batchsize ${BATCHSIZE} \
    --selectionlist ${SELECTIONS} \

echo "Copying outputs to destination ${STORAGE} (overwriting enabled)"
for output in *batch${JOBID}.root
do
    xrdcopy -pf ${output} ${STORAGE}/batch${JOBID}/
done
