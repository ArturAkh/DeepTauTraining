#!/usr/bin/env python

import yaml
import numpy as np
import re
import argparse

types = ['electron', 'muon', 'jet', 'genuine']
pileup = ['NoPU', 'PU140', 'PU200']

def construct_binning(binning_structure):
    bins = np.concatenate([np.arange(start, end, step) for start, end, step in binning_structure] + [np.array([binning_structure[-1][1]])])
    return bins

def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect: alphanumeric sort (in bash, that's 'sort -V')"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def create_selections(ptabsetabinsfile):
    binning = yaml.load(open(ptabsetabinsfile, 'r'), Loader=yaml.FullLoader)

    ptbins  = construct_binning(binning['pt'])
    absetabins = construct_binning(binning['abseta'])

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
        selection = ""
        if t == "electron":
            selection = "genLepton_index >= 0 && (genLepton_kind == 1 || genLepton_kind == 3)"
        elif t == "muon":
            selection = "genLepton_index >= 0 && (genLepton_kind == 2 || genLepton_kind == 4)"
        elif t == "jet":
            selection = "genLepton_index == -1"
        elif t == "genuine":
            selection = "genLepton_index >= 0 && genLepton_kind == 5"
        typeselections[t] = selection

    selections = {}

    for t in typeselections:
        for i, absetabin in enumerate(absetaselections):
            for j, ptbin in enumerate(ptselections):
                selection = ' && '.join([typeselections[t], absetabin, ptbin])
                sname = '%s_absetabin%s_ptbin%s'%(t, str(i), str(j))
                selections[sname] = selection

    return selections


def create_parser(mode=None):
    parser = argparse.ArgumentParser(description='Create batches with equal number of entries per selection of Taus.')
    parser.add_argument('--prod-campaign', required=True, help='TauTuple production campaign. Used to strip off the input path.')
    parser.add_argument('--process-types', required=True, help='Configuration .yaml file with settings, which types use for which process.')
    parser.add_argument('--pt-abseta-bins', required=True, help='Configuration .yaml file with settings for pt and abs(eta) bins.')
    if mode == 'fileinfo':
        parser.add_argument('--input-files', required=True, nargs='+', help='input TauTuple ROOT files.')
        parser.add_argument('--job', required=True, type=int, help= 'Index of the job processed.')
    elif mode == 'filedatabase':
        parser.add_argument('--input-file-list', required=True, help='input TauTuple ROOT files.')
        parser.add_argument('--parallel', type=int, default=10, help= 'Number of parallel processed jobs. Default: %(default)s')
        parser.add_argument('--files-per-job', type=int, default=20, help= 'Number of files to be checked per job. Default: %(default)s')
        parser.add_argument('--replace-file-prefix', default=':', help='Prefix of file path to be replaced, to be used in the following "<old-prefix>:<new-prefix>". Default: %(default)s')
        parser.add_argument('--recompute-infos', action='store_true', help='To be used in case .json output files with "counts_job_*.json" are not available yet.')
    elif mode == 'jobdatabase':
        parser.add_argument('--pileup', required=True, choices=['NoPU', 'PU140', 'PU200', 'all', 'none'], help='Which explicit pileup scenarios to be used for training based on balanced batches.')
        parser.add_argument('--events-per-batch-type', required=True, type=int, help='Number of events per individual batch-type (process x tautype x ptabsetabin)')
        parser.add_argument('--jobconfigs-directory', required=True, help='Absolute path to the directory, where to put configuration files for each job.')
    return parser
