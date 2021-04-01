#!/usr/bin/env python

import sys
import os
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
        ptabsetabins = [(k,v) for k,v in finfo.items() if not k in ['process','pileup','path']]
        for k,v in ptabsetabins:
            summary_info[identifier].setdefault(k,0)
            summary_info[identifier][k] += v

    json.dump(summary_info, open('summary.json','w'), sort_keys=True, indent=4)

    process_types = yaml.load(open(args.process_types, 'r'), Loader=yaml.FullLoader)
    pulist = pileup if args.pileup == 'all' else [args.pileup]

    minima = []
    maxima = []
    filesforselectiondatabase = {}
    tauoffsets = {}

    for p in process_types.keys():
        for pu in pulist:
            prockey = '_'.join([p,pu]) if pu != 'none' else p
            ptabsbetabins = summary_info.get(prockey)
            if ptabsbetabins:
                chosen_ptabsbetabins = [(k,v) for k,v in ptabsbetabins.items() if k.split('_')[0] in process_types[p]['active_types']]
                if len(chosen_ptabsbetabins) > 0:
                    minima.append((prockey, chosen_ptabsbetabins[np.argmin([v for k,v in chosen_ptabsbetabins])]))
                    maxima.append((prockey, chosen_ptabsbetabins[np.argmax([v for k,v in chosen_ptabsbetabins])]))
                    filesforselectiondatabase[prockey] = {}
                    tauoffsets[prockey] = {}
                    for b in ptabsbetabins:
                        filesforselectiondatabase[prockey][b] = []
                        tauoffsets[prockey][b] = { 'fileindex' : 0, 'tauoffset' : 0}
    
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

    for finfo in counts.values():
        prockey = None
        if finfo['pileup'] in pulist:
            prockey = '_'.join([finfo['process'],finfo['pileup']])
        elif pulist == ['none']:
            prockey = finfo['process']
        if prockey in filesforselectiondatabase:
            for key,value in [(k,v) for k,v in finfo.items() if not k in ['process','pileup','path'] and v > 0 and k.split('_')[0] in process_types[finfo['process']]['active_types']]:
                filesforselectiondatabase[prockey][key].append({'path' : finfo['path'], 'nevents' : value})

    for prockey in filesforselectiondatabase:
        for selection in list(filesforselectiondatabase[prockey].keys()):
            if len(filesforselectiondatabase[prockey][selection]) == 0:
                filesforselectiondatabase[prockey].pop(selection)
    
    json.dump(filesforselectiondatabase, open('filesforselection.json','w'), sort_keys=True, indent=4)

    n_batches = int(total_maximum[1][1]/args.events_per_batch_type)
    print(f'Desired number of batches: {n_batches}')

    os.makedirs(args.jobconfigs_directory, exist_ok = True)
    confignames = []

    for jobindex in range(n_batches):
        sys.stdout.write(f'\rCreating job: {jobindex}')
        sys.stdout.flush()
        jobdatabase = {'binning' : args.pt_abseta_bins, 'jobindex': jobindex}
        for prockey in filesforselectiondatabase:
            jobdatabase[prockey] = {}
            for selection in filesforselectiondatabase[prockey]:
                n_files = len(filesforselectiondatabase[prockey][selection])
                if n_files > 0:
                    offset = tauoffsets[prockey][selection]['tauoffset']
                    jobdatabase[prockey][selection] = { 'files' : [], 'range' : [offset, offset + args.events_per_batch_type] }
                    n_aggregated_events = - offset
                    absolute_fileindex = tauoffsets[prockey][selection]['fileindex']
                    relative_fileindex = tauoffsets[prockey][selection]['fileindex']
                    while n_aggregated_events < args.events_per_batch_type:
                        jobdatabase[prockey][selection]['files'].append(filesforselectiondatabase[prockey][selection][relative_fileindex]['path'])
                        n_aggregated_events += filesforselectiondatabase[prockey][selection][relative_fileindex]['nevents']
                        absolute_fileindex += 1
                        relative_fileindex = absolute_fileindex % n_files
                    leftover = n_aggregated_events - args.events_per_batch_type
                    if leftover != 0:
                        absolute_fileindex -= 1
                        relative_fileindex = absolute_fileindex % n_files
                        tauoffsets[prockey][selection]['tauoffset'] = filesforselectiondatabase[prockey][selection][relative_fileindex]['nevents']  - leftover
                    tauoffsets[prockey][selection]['fileindex'] = relative_fileindex
        configname = os.path.join(args.jobconfigs_directory,f'job_{jobindex}.json')
        json.dump(jobdatabase, open(configname, 'w'), sort_keys=True, indent=4)
        confignames.append(configname)

    print('Saving paths to configuration files in arguments.txt file.')
    with open('arguments.txt','w') as out:
        out.write('\n'.join(confignames))
    print('Saving required environment variables in a .sh file to be sourced.')
    envcontent = []
    envcontent.append(f'export BALANCED_BATCHES_OUTPUTDIR={args.output_directory}')
    print(f"\tBALANCED_BATCHES_OUTPUTDIR = {args.output_directory}")
    with open('additional_environment.sh','w') as out:
        out.write('\n'.join(envcontent))
        out.close()

    print('Creating htcondor folder for logging')
    os.makedirs('logging', exist_ok = True)
