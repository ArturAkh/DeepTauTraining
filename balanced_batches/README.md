# Creating balanced batches
The set of scripts in this folderallows to construct training inputs for `DeepTau`,
which are balanced with respect to a specified phase-space. In that special case we
balance:

* per process in an event,
* per true type of &tau;<sub>h</sub> candidate,
* per p<sub>T</sub>(&tau;<sub>h</sub>) slice,
* and per |&eta;(&tau;<sub>h</sub>)| slice.

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

## Number of events in files for each phase-space region to be balanced

In the first step, it is important to figure out, how many events are contained in an input file, which
belongs to a certain phase-space region. This task can be covered by the following command:

```bash
python create_database.py --prod-campaign prod_Phase2_v2 \
                          --process-types prod_Phase2_v2/process_types.yaml \
                          --pt-abseta-bins prod_Phase2_v2/binning.yaml \
                          --input-file-list  prod_Phase2_v2/flist.txt \
                          --replace-file-prefix "/storage/gridka-nrg/@root://cmsxrootd-kit.gridka.de//store/user/" \
                          --recompute-infos
```

This command will use the script `check_inputs.py` to determine for each file in the filelist `prod_Phase2_v2/flist.txt` the number of events per
phase-space region, which is configured through the files `prod_Phase2_v2/process_types.yaml` and `prod_Phase2_v2/binning.yaml`. A replacement
of the file prefix is done to access the files via XRootD. By default, 20 files per job are processed, with 10 jobs in parallel on a local machine.
After the outputs of each job, `counts_job_*.json`, are prepared (using the option `--recompute-infos`), they are summarized into the `counts.json` database.

Feel free to check the available options for the scripts `create_database.py` and `check_inputs.py`. Beyond that, have a look at the `.yaml` configuration files
and adapt them for your purpose.

## Constructing database for jobs, which create balanced batches
