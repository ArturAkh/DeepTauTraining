import os
import sys
import json
import datetime
#import tracemalloc

import ROOT as r
r.gROOT.SetBatch()
r.gROOT.ProcessLine('gErrorIgnoreLevel = 2001;')

from utils import create_selections

#tracemalloc.start()
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
        fname = '_'.join([prockey,selname,f"batch{jobconf['jobindex']}.root"])
        #current, peak = tracemalloc.get_traced_memory()
        #print(f'\tCreating batch {fname}', datetime.datetime.now(), f'memory usage: current={round(current/1024**2,1)}MB, peak={round(peak/1024**2,1)}MB')
        print(f'\tCreating batch {fname}', datetime.datetime.now())
        df = r.RDataFrame('taus', jobconf[prockey][selname]['files'])
        df.Filter(selections[selname]).Range(jobconf[prockey][selname]['range'][0], jobconf[prockey][selname]['range'][1]).Snapshot('taus',fname)

print('Batch creation finished', datetime.datetime.now())
#tracemalloc.stop()
