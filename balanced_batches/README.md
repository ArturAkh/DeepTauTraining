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

In the next step, configuration files are created for jobs, which create balanced batches.

At first, only a `summary.json` file is created with the command below, to judge, which &tau;<sub>h</sub> types (`genuine`, `jet`, `electron`, `muon`) to consider for a certain process.
Its content is the amount of events in total per phase-space region. This allows then to adapt the corresponding configuration in `prod_Phase2_v2/process_types.yaml` in this example with,
e.g. to avoid `muon` types for `ZPrimeToEE` samples.

```bash
python create_batchjobs.py --prod-campaign prod_Phase2_v2 \
                           --process-types prod_Phase2_v2/process_types.yaml \
                           --pt-abseta-bins prod_Phase2_v2/binning.yaml \
                           --pileup PU200 \
                           --events-per-batch-type 15 \
                           --jobconfigs-directory /ceph/akhmet/balanced_batches_configs/ \
                           --output-directory "srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only//store/user/aakhmets/TauML/prod_Phase2_v2/balanced_batches/" \
                           --summary-only
```

After adapting `prod_Phase2_v2/process_types.yaml`, the command can be executed to create configuration files for each file by neglecting the `--summary-only` option:

```bash
python create_batchjobs.py --prod-campaign prod_Phase2_v2 \
                           --process-types prod_Phase2_v2/process_types.yaml \
                           --pt-abseta-bins prod_Phase2_v2/binning.yaml \
                           --pileup PU200 \
                           --events-per-batch-type 15 \
                           --jobconfigs-directory /ceph/akhmet/balanced_batches_configs/ \
                           --output-directory "srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only//store/user/aakhmets/TauML/prod_Phase2_v2/balanced_batches/"
```

The first three options are as used in the previous section. The remaining options have the following meaning:

* `--pileup`: is used to limit the training to a specific PU scenario. Can be ignored by setting to `none`.
* `--events-per-batch-type`: number of events in a certain phase-space region, that should be included into the balanced batch output file of a job. During the creation of
the configurarion files, it is taken into account, that in case there are in total less events in a region than requested, then the associated input files will be used multiple
times. It is also kept track of which files and which events to use for a job by keeping the required file index and event offset to be used for a region. Feel free to have a closer
look at the script `create_batchjobs.py`. In the current state, the number of balanced batches is computed from maximum number of events in a phase-space region and the requested number
of events per batch type.
* `--jobconfigs-directory`: output directory for configuration files. Make sure, that you have several GB space there, since all configuration files together can require about 10 GB or more.
* `--output-directory`: output directory for balanced batches ROOT files. Can be declared as remote (e.g. with `srm`) or local, since `gfal-copy` is used for the copy operation.

## Submitting jobs for balanced batches

In the final step, the submission of jobs is performed, using HTCondor configuration files, for example via:

```bash
condor_submit condor_config_ETP.jdl
```

This file will use the `arguments.txt` file to pass the configuration file of a job to the top-level script `run_jobs.sh`. In case only a limited amount of jobs is allowed for a user
on a batch system, feel free to split `arguments.txt` in parts and submit them sequentially.

Within each job, the top-level script `run_jobs.sh` performs the following steps:

* `run_batches.sh`:
  * Sets up the LCG environment stack
  * Runs the `make_batches.py` script with appropriate `job*.json` configuration file
  * Merges the indivudual outputs to a single balanced batch ROOT file
* `copy_batches.sh`:
  * Sets up a (separate) grid environment
  * copies over the balanced batch ROOT file to the configured output directory

To test that workflow locally, you can perform in a **fresh** terminal:

```bash
./run_jobs.sh `head -n 1 arguments.txt`
```

Keep in mind, that such a job can take up to 48 hours, so change `make_batches.py` script appropriately for testing, e.g. by putting `break` into the two `for`-loops, which create the output file at
the end of the script:

```python
    for prockey in [k for k in jobconf if not k in ['binning','jobindex']]:
        for selname in jobconf[prockey]:
            # ... omitted code ...
            break
        break
```
