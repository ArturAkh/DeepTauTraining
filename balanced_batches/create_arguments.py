import json
import argparse
import re

def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect: alphanumeric sort (in bash, that's 'sort -V')"""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

parser = argparse.ArgumentParser(description='Create batches with equal number of entries per selection of Taus.')

parser.add_argument('--countinfo', required=True, help='Information .json file with counts for (pt, abs(eta), type) selections of Taus.')
parser.add_argument('--storage', required=True, help= 'Path to folder on dCache with write access.')
parser.add_argument('--nselections', required=True, type=int, help= 'Number of of selections to be used to create batches within a job.')
parser.add_argument('--njobs', required=True, type=int, help= 'Number of jobs to be processed.')
parser.add_argument('--batchsize', required=True, type=int, help= 'Batch size to be created for each selection. If too big, a minimum corresponding to a selection is taken.')

args = parser.parse_args()

with open(args.countinfo, 'r') as incounts:
    countinfo = sorted_nicely(json.load(incounts).keys())

lines = []
line_template = "{JOBID} {BATCHSIZE} {SELECTIONS} {STORAGE}"

for jobid in range(args.njobs):
    length = len(countinfo)
    start = 0
    end = start + args.nselections
    while end < length:
        selections = ",".join(countinfo[start:end])
        start += args.nselections
        end += args.nselections
        lines.append(line_template.format(JOBID=jobid, BATCHSIZE=args.batchsize, SELECTIONS=selections, STORAGE=args.storage))
    selections = ",".join(countinfo[start:])
    lines.append(line_template.format(JOBID=jobid, BATCHSIZE=args.batchsize, SELECTIONS=selections, STORAGE=args.storage))

with open("arguments.txt", "w") as out:
    out.write("\n".join(lines))
