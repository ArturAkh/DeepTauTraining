# Creating balanced batches
The set of scripts in this folders allows to construct training inputs for `DeepTau`,
which are balanced with respect to a specified phasespace. In that special case we
balance:

* per process in an event,
* per true type of &tau;<sub>h</sub> candidate,
* per p<sub>T</sub> slice,
* and per |&eta;| slice.

Based on the provided settings, the aim is to achieve a uniform distribution of
events across the phase-space regions defined for balance above.

In the following, the technical instructions are given to produce balanced batches
out of `TauTuple` n-tuples produced with [TauMLTools](https://github.com/cms-tau-pog/TauMLTools).

The software explained and documented here is optimized for an efficient processing
on a large number of input files on HTCondor batch system resources,
while reading in only required files per job and using small amount of memory.

## Software setup and prerequisites

To use the software in this package you need the following:

* A working mount to `/cvmfs/cms.cern.ch` and `/cvmfs/grid.cern.ch/` both on your login worker
node and on the nodes of the HTCondor batch system you are using.
* A valid grid computing certificate

To install the package, you only need to download it via `git`:

```bash
git clone git@github.com:ArturAkh/DeepTauTraining.git
```

To setup the required environment, you need to execute the following commands:

```bash
cd DeepTauTraining/balanced_batches

# Currently (01.04.2021) latest `python3`-based software stack with `ROOT`
source /cvmfs/sft.cern.ch/lcg/views/LCG_99/x86_64-centos7-gcc10-opt/setup.sh

# assuming you have created one at that path with 'voms-proxy-init'
export X509_USER_PROXY=/path/to/your/grid-proxy.pem
```

After this, you should be ready to go.

## Number of events in files for each phasespace region to be balanced
