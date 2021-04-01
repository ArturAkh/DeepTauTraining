import os
import sys
import json
import datetime
from multiprocessing import Process

import ROOT as r
r.gROOT.SetBatch()
r.gROOT.ProcessLine('gErrorIgnoreLevel = 2001;')

from utils import create_selections

def create_output_for_batch_type(fname, selection, files, taurange):
    df = r.RDataFrame('taus', files)
    df.Filter(selection).Range(taurange[0], taurange[1]).Snapshot('taus',fname)

def main():
    print('Starting batch creation', datetime.datetime.now())

    jobconfig = sys.argv[1]

    if not os.path.exists(jobconfig):
        jobconfig = os.path.basename(jobconfig)
    jobconf = json.load(open(jobconfig, 'r'))

    binningfile = jobconf['binning']
    if not os.path.exists(binningfile):
        binningfile = os.path.basename(binningfile)

    selections = create_selections(binningfile)

    for prockey in [k for k in jobconf if not k in ['binning','jobindex']]:
        for selname in jobconf[prockey]:
            info = {}
            fname = '_'.join([prockey,selname,f"batch{jobconf['jobindex']}.root"])
            print(f'\tCreating batch {fname}', datetime.datetime.now())
            p = Process(target=create_output_for_batch_type, args=(fname, selections[selname], jobconf[prockey][selname]['files'], jobconf[prockey][selname]['range']))
            p.start()
            p.join()

    print('Batch creation finished', datetime.datetime.now())

if __name__ == '__main__': main()
