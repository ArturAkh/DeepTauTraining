#!/usr/bin/env python

import json
import re

import numpy as np
import ROOT as r
r.gROOT.SetBatch()
r.gROOT.ProcessLine('gErrorIgnoreLevel = 2001;')

from utils import types, pileup, processes
from utils import create_selections, create_parser

if __name__ == '__main__':

    parser = create_parser(mode='fileinfo')
    args = parser.parse_args()

    selections = create_selections(args.pt_abseta_bins)

    info = {}
    for inputfile in args.input_files:
        filename = inputfile[inputfile.find(args.prod_campaign):].replace('/crab_output','')
        info[filename] = {}

        for proc in processes:
            if re.search(processes[proc],filename):
                info[filename]['process'] = proc
                break

        for pu in pileup:
            if pu in filename:
                info[filename]['pileup'] = pu
                break
        
        counts = {}

        df = r.RDataFrame('taus', inputfile, ["genLepton_index", "genLepton_kind", "tau_pt", "tau_eta"])
        for name,s in selections.items():
            counts[name] = df.Filter(s).Count()

        for name in selections:
            info[filename][name] = counts[name].GetValue()

    outname = f'counts_job_{args.job}.json'
    json.dump(info, open(outname,'w'), sort_keys=True, indent=4)
