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

def construct_binning(binning_structure):
    bins = np.concatenate([np.arange(start, end, step) for start, end, step in binning_structure] + [np.array([binning_structure[-1][1]])])
    return bins

def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect: alphanumeric sort (in bash, that's 'sort -V')"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

parser = argparse.ArgumentParser(description='Create batches with equal number of entries per selection of Taus.')

parser.add_argument('--filelist', required=True, help='Filelist .txt file for input TauTuple files.')
parser.add_argument('--ptabsetabins', required=True, help='Configuration .yaml file with settings for pt and abs(eta) bins.')
parser.add_argument('--countinfo', required=True, help='Information .json file with counts for (pt, abs(eta), type) selections of Taus.')
parser.add_argument('--selectionlist', required=True, help= 'Name list of selections (separated by comma) to be used to create batches.')
parser.add_argument('--job', required=True, type=int, help= 'Index of the job processed.')
parser.add_argument('--batchsize', required=True, type=int, help= 'Batch size to be created for each selection. If too big, a minimum corresponding to a selection is taken.')

args = parser.parse_args()

binning = yaml.load(open(args.ptabsetabins, 'r'), Loader=yaml.FullLoader)

flist = [f.strip() for f in open(args.filelist, 'r').readlines()]
fnames = r.std.vector('string')()
for n in flist:
    fnames.push_back(n)

df = r.RDataFrame('taus', fnames)

ptbins  = construct_binning(binning['pt'])
absetabins = construct_binning(binning['abseta'])
types = ['electron', 'muon', 'jet', 'genuine']

ptselections = []
absetaselections = []
typeselections = {}

for ptlow, pthigh in zip(ptbins[:-1], ptbins[1:]):
    ptselections.append('(tau_pt >= {LOW} && tau_pt < {HIGH})'.format(LOW=ptlow,HIGH=pthigh))
ptselections.append('(tau_pt >= {HIGH})'.format(HIGH=ptbins[-1]))

for absetalow, absetahigh in zip(absetabins[:-1], absetabins[1:]):
    absetaselections.append('(abs(tau_eta) >= {LOW} && abs(tau_eta) < {HIGH})'.format(LOW=absetalow,HIGH=absetahigh))
absetaselections.append('(abs(tau_eta) >= {HIGH})'.format(HIGH=absetabins[-1]))

for t in types:
    selection = ''
    if t == 'electron':
        selection = '(lepton_gen_match == 1 || lepton_gen_match == 3)'
    elif t == 'muon':
        selection = '(lepton_gen_match == 2 || lepton_gen_match == 4)'
    elif t == 'jet':
        selection = '(lepton_gen_match == 6)'
    elif t == 'genuine':
        selection = '(lepton_gen_match == 5)'
    typeselections[t] = selection

fdfs = {}

selections = {}

for t in typeselections:
    for i, absetabin in enumerate(absetaselections):
        for j, ptbin in enumerate(ptselections):
            selection = ' && '.join([typeselections[t], absetabin, ptbin])
            sname = '%s_absetabin%s_ptbin%s'%(t, str(i), str(j))
            selections[sname] = selection

for sname in set(selections.keys()).intersection(set(args.selectionlist.split(','))):
            fdfs[sname] = df.Filter(selections[sname])

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
