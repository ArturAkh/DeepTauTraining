import ROOT as r
import json
import numpy as np
import glob
from multiprocessing import Pool
r.gROOT.SetBatch()

#fpath = "/storage/gridka-nrg/aakhmets/TauML/crab_output/SingleElectron_PT200to500/crab_SingleElectron_PT200to500_PU200/200914_145104/0000/eventTuple_1.root"

filelist = glob.glob("/storage/gridka-nrg/aakhmets/TauML/crab_output/*/*PU140*/*/*/*.root")

def construct_binning(binning_structure):
    bins = np.concatenate([np.arange(start, end, step) for start, end, step in binning_structure] + [np.array([binning_structure[-1][1]])])
    return bins

def construct_info(fpath):
    ptbins  = construct_binning([[20.0, 60.0, 5.0], [60.0, 100.0, 10.0]])
    absetabins = construct_binning([[0.0, 2.4, 0.6]])
    types = ["electron", "muon", "jet", "genuine"]

    ptselections = []
    absetaselections = []
    typeselections = {}

    for ptlow, pthigh in zip(ptbins[:-1], ptbins[1:]):
        ptselections.append("(tau_pt >= {LOW} && tau_pt < {HIGH})".format(LOW=ptlow,HIGH=pthigh))
    ptselections.append("(tau_pt >= {HIGH})".format(HIGH=ptbins[-1]))

    for absetalow, absetahigh in zip(absetabins[:-1], absetabins[1:]):
        absetaselections.append("(abs(tau_eta) >= {LOW} && abs(tau_eta) < {HIGH})".format(LOW=absetalow,HIGH=absetahigh))
    absetaselections.append("(abs(tau_eta) >= {HIGH})".format(HIGH=absetabins[-1]))


    for t in types:
        selection = ""
        if t == "electron":
            selection = "(lepton_gen_match == 1 || lepton_gen_match == 3)"
        elif t == "muon":
            selection = "(lepton_gen_match == 2 || lepton_gen_match == 4)"
        elif t == "jet":
            selection = "(lepton_gen_match == 6)"
        elif t == "genuine":
            selection = "(lepton_gen_match == 5)"
        typeselections[t] = selection

    df = r.RDataFrame("taus", fpath, ["lepton_gen_match", "tau_pt", "tau_eta"])

    info = {}

    #selections = []
    #
    #def compute_info(information):
    #    print(information["selection"])
    #    value = information["dataframe"].Filter(information["selection"]).Count().GetValue()
    #    return { information["name"] : value }
    #
    #for t in typeselections:
    #    for i, absetabin in enumerate(absetaselections):
    #        for j, ptbin in enumerate(ptselections):
    #            selection = " && ".join([typeselections[t], absetabin, ptbin])
    #            selections.append({"name" : "%s_absetabin%s_ptbin%s"%(t, str(i), str(j)), "selection" : selection, "dataframe" : df})

    for t in typeselections:
        for i, absetabin in enumerate(absetaselections):
            for j, ptbin in enumerate(ptselections):
                selection = " && ".join([typeselections[t], absetabin, ptbin])
                info["%s_absetabin%s_ptbin%s"%(t, str(i), str(j))] = df.Filter(selection).Count().GetValue()
    return (fpath , info)

complete_info = {}
p = Pool(15)
outputs = p.map(construct_info, filelist)
for out in outputs:
    complete_info[out[0]] = out[1]

with open("info.json", "w") as f:
    json.dump(complete_info, f, indent=2, sort_keys=True)
