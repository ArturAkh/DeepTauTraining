#!/usr/bin/env python

import json
import yaml
import numpy as np

from utils import create_parser, pileup

if __name__ == '__main__':

    parser = create_parser(mode='jobdatabase')
    args = parser.parse_args()

    countsf = open('counts.json')
    counts = json.load(countsf)
    countsf.close()

    summary_info = {}
    for fpath,finfo in counts.items():
        identifier = '_'.join([finfo['process'],finfo['pileup']])
        summary_info.setdefault(identifier,{})
        ptabsetabins = [(k,v) for k,v in finfo.items() if not k in ['process','pileup']]
        for k,v in ptabsetabins:
            summary_info[identifier].setdefault(k,0)
            summary_info[identifier][k] += v

    json.dump(summary_info, open('summary.json','w'), sort_keys=True, indent=4)

    process_types = yaml.load(open(args.process_types, 'r'), Loader=yaml.FullLoader)
    pulist = pileup if args.pileup == 'all' else [args.pileup]

    minima = []
    maxima = []
    filesforselectiondatabase = {}

    for p in process_types.keys():
        for pu in pulist:
            prockey = '_'.join([p,pu]) if pu != 'none' else p
            ptabsbetabins = summary_info.get(prockey)
            if ptabsbetabins:
                chosen_ptabsbetabins = [(k,v) for k,v in ptabsbetabins.items() if k.split('_')[0] in process_types[p]['active_types']]
                minima.append((prockey, chosen_ptabsbetabins[np.argmin([v for k,v in chosen_ptabsbetabins])]))
                maxima.append((prockey, chosen_ptabsbetabins[np.argmax([v for k,v in chosen_ptabsbetabins])]))
                filesforselectiondatabase[prockey] = {}
                for b in ptabsbetabins:
                    filesforselectiondatabase[prockey][b] = []
    
    print('Minima per process:')
    for pm in minima:
        print('\t',pm)
    print('Maxima per process:')
    for pm in maxima:
        print('\t',pm)

    total_minimum = minima[np.argmin([v for (p, (k,v)) in minima])]
    total_maximum = maxima[np.argmax([v for (p, (k,v)) in maxima])]
    n_minmax_batches = int(total_maximum[1][1]/total_minimum[1][1])

    print('Total mininum:',total_minimum)
    print('Total maximum:',total_maximum)
    print('Number of max/min batches:',n_minmax_batches)
    
    if args.pileup in pileup:
        n_ptabsetabins = int(len(summary_info[total_minimum[0]].keys()) / 4)
        n_proctypes = np.sum([len(v['active_types']) for k,v in process_types.items() if summary_info.get('_'.join([k,args.pileup]))])
        n_events_per_minmax_batch = total_minimum[1][1] * n_ptabsetabins * n_proctypes
        print('Number of events per max/min batch:',n_events_per_minmax_batch)
    
    jobdatabase = {}
