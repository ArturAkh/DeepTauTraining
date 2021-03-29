import sys
import json
import yaml
import datetime
import argparse

import re
import numpy as np
import ROOT as r
r.gROOT.SetBatch()
r.gROOT.ProcessLine('gErrorIgnoreLevel = 2001;')

job = args.job
countinfo = {}
with open(args.countinfo, 'r') as incounts:
    countinfo = json.load(incounts)
selectionsize = min(countinfo.values())
batchsize = min(selectionsize, args.batchsize)
if selectionsize < args.batchsize:
    print "Warning: the batch size %s chosen is too large. Setting to the minimum size of a selection, %s."%(args.batchsize, batchsize)
for sname in sorted_nicely(fdfs):
    selectioncount = countinfo[sname]
    nbatches = selectioncount // batchsize
    start = job % nbatches
    end = start + 1
    name = sname + '_batch%s.root'%(job)
    print 'Creating batch %s for'%(job), sname, datetime.datetime.now()
    fdfs[sname].Range(start * batchsize, end * batchsize).Snapshot('taus', name)

print 'finished'
