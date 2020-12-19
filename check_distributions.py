import ROOT as r
import yaml
import numpy as np
import glob
r.gROOT.SetBatch()
r.gROOT.ProcessLine('gErrorIgnoreLevel = 2001;')
r.gStyle.SetOptStat("uo")

def construct_binning(binning_structure):
    bins = np.concatenate([np.arange(start, end, step) for start, end, step in binning_structure] + [np.array([binning_structure[-1][1]])])
    return bins

binning = yaml.load(open("binning.yaml", 'r'), Loader=yaml.FullLoader)
ptbins  = construct_binning(binning['pt'])

taus = r.TChain("taus") 
flist = glob.glob("/storage/gridka-nrg/aakhmets/TauML/balanced_batches/batch0/genuine*batch0.root")
for f in flist:
    taus.Add(f)
print taus.GetEntries()
#jets = 
#muons = 
#electrons = 

c = r.TCanvas()
c.cd()

h = r.TH1D("h", "h", len(ptbins)-1, ptbins)

taus.Draw("tau_pt>>h", "", "goff")
h.Draw("hist")
c.SaveAs("pt_taus_hist.png")
c.Clear()

taus.Draw("tau_pt", "", "hist")
c.SaveAs("pt_taus.png")
c.Clear()

taus.Draw("tau_eta", "", "hist")
c.SaveAs("eta_taus.png")
c.Clear()
