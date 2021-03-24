import yaml
import numpy as np
import re
import argparse

types = ['electron', 'muon', 'jet', 'genuine']
pileup = ['NoPU', 'PU140', 'PU200']
processes = {
    'DY' : 'DYToLL',
    'WJets' : 'WJetsToLNu',
    'ElecGun' : '(Double|Single)Electron',
    'MuonGun' : '(DoubleMuon|MuMinus|MuPlus)',
    'ggH' : 'GluGluHToTauTau',
    'VBFH' : 'VBFHToTauTau',
    'MinBias' : 'MinBias',
    'QCD' : 'QCD',
    'TTTo2L2Nu' : 'TTTo2L2Nu',
    'TTToSemiLepton' : 'TTToSemiLepton',
    'TT' : 'TT_',
    'ZprimeToEE_M-6000' : 'ZprimeToEE_M-6000',
    'ZprimeToMuMu_M-6000' : 'ZprimeToMuMu_M-6000',
    'ZprimeToTauTau_M-500' : 'ZprimeToTauTau_M-500',
    'ZprimeToTauTau_M-1500' : 'ZprimeToTauTau_M-1500',
}

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
    parser.add_argument('--prodcampaign', required=True, help='TauTuple production campaign. Used to strip off the input path.')
    if mode == 'fileinfo':
        parser.add_argument('--ptabsetabins', required=True, help='Configuration .yaml file with settings for pt and abs(eta) bins.')
        parser.add_argument('--filelist', required=True, nargs='+', help='input TauTuple ROOT files.')
        parser.add_argument('--job', required=True, type=int, help= 'Index of the job processed.')
    #parser.add_argument('--filelist', required=True, help='Filelist .txt file for input TauTuple files.')
    #parser.add_argument('--countinfo', required=True, help='Information .json file with counts for (pt, abs(eta), type) selections of Taus.')
    #parser.add_argument('--selectionlist', required=True, help= 'Name list of selections (separated by comma) to be used to create batches.')
    #parser.add_argument('--job', required=True, type=int, help= 'Index of the job processed.')
    #parser.add_argument('--batchsize', required=True, type=int, help= 'Batch size to be created for each selection. If too big, a minimum corresponding to a selection is taken.')
    return parser
