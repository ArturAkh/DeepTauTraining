#!/usr/bin/env python

import os
import json
import numpy as np
from multiprocessing import Pool

from utils import create_parser

def check_inputs_job(info):
    files = ' '.join(info['files'])
    cmd = f"python check_inputs.py --pt-abseta-bins {info['binning']} --input-files {files} --prod-campaign {info['campaign']} --job {info['jobindex']}"
    return os.WEXITSTATUS(os.system(cmd))
    

if __name__ == '__main__':

    parser = create_parser(mode='filedatabase')
    args = parser.parse_args()
    old_prefix, new_prefix = args.replace_file_prefix.split(':')

    flist = open(args.input_file_list,'r')
    filelist = [f.strip().replace(old_prefix,new_prefix) for f in flist.readlines()]
    flist.close()

    info_list = []

    jobindex = 0
    while len(filelist) > args.files_per_job:
        poplist, filelist = filelist[:args.files_per_job], filelist[args.files_per_job:]
        info = {}
        info['jobindex'] = jobindex
        info['files'] = poplist
        info['binning'] = args.pt_abseta_bins
        info['campaign'] = args.prod_campaign
        info_list.append(info)
        jobindex += 1
    info = {}
    info['jobindex'] = jobindex
    info['files'] = filelist
    info['binning'] = args.pt_abseta_bins
    info['campaign'] = args.prod_campaign
    info_list.append(info)

    if args.recompute_infos:
        p = Pool(args.parallel)
        exitcodes = p.map(check_inputs_job, info_list)
        print("Exitcodes from jobs:",exitcodes)
        if np.sum(exitcodes) > 0:
            print(f'ERROR: Computation failed for at least one job!')
            exit(1)

    aggregated_info = {}

    for index in range(len(info_list)):
        jsonpath = f'counts_job_{index}.json'
        if os.path.exists(jsonpath):
            with open(jsonpath,'r') as jsonf:
                aggregated_info.update(json.load(jsonf))
        else:
            print(f'ERROR: {jsonpath} does not exist!')
            exit(1)

    json.dump(aggregated_info, open('counts.json','w'), sort_keys=True, indent=4)
    
