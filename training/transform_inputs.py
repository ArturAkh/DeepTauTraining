import uproot
import uproot_methods
import glob
import awkward as ak
import numpy as np
import yaml
import matplotlib.pyplot as plt

plotting = True

#flist = glob.glob('/ceph/akhmet/balanced_batches/batch0/*.root')
flist = glob.glob('/ceph/akhmet/balanced_batches/batch0/*.root')[0:3]

transformation_dict = yaml.load(open('transformed_quantities.yaml', 'r'), Loader=yaml.FullLoader)

n_pop_events = 10
tables = {}

def transform_minmax(values, minval, maxval):
    return (np.clip(values, minval, maxval) - minval)/(maxval - minval)

def safe_ratio(numerator, denominator):
    nonnull_denominator = denominator != 0.
    denominator = denominator * nonnull_denominator + np.invert(nonnull_denominator)
    numerator *= nonnull_denominator
    return numerator / denominator

for f in flist:
    print(f)
    tables[f] = ak.Table(uproot.open(f)['taus'].arrays(namedecode='utf-8'))

## create a table with 10 events for each class from batch 0
batchtable = ak.concatenate([tables[f][:n_pop_events] for f in flist])

## compute new quantities based on inputs

### generator truth
batchtable['gen_e'] = np.equal(batchtable['lepton_gen_match'], 1) + np.equal(batchtable['lepton_gen_match'], 3)
batchtable['gen_mu'] = np.equal(batchtable['lepton_gen_match'], 2) + np.equal(batchtable['lepton_gen_match'], 4)
batchtable['gen_tau'] = np.equal(batchtable['lepton_gen_match'], 5)
batchtable['gen_jet'] = np.equal(batchtable['lepton_gen_match'], 6)

### hadronic tau related quantities
batchtable['tau_p4'] = uproot_methods.TLorentzVectorArray.from_ptetaphim(
    batchtable['tau_pt'],
    batchtable['tau_eta'],
    batchtable['tau_phi'],
    batchtable['tau_mass']
)
batchtable['tau_E_over_pt'] = batchtable['tau_p4'].E / batchtable['tau_pt']
batchtable['tau_n_charged_prongs'] = batchtable['tau_decayMode'] // 5 + 1 
batchtable['tau_n_neutral_prongs'] = batchtable['tau_decayMode'] % 5
batchtable['chargedIsoPtSumdR03_over_dR05'] = safe_ratio(batchtable['chargedIsoPtSumdR03'], batchtable['chargedIsoPtSum'])
batchtable['neutralIsoPtSumWeight_over_neutralIsoPtSum'] = safe_ratio(batchtable['neutralIsoPtSumWeight'], batchtable['neutralIsoPtSum'])
batchtable['neutralIsoPtSumWeightdR03_over_neutralIsoPtSum'] = safe_ratio(batchtable['neutralIsoPtSumWeightdR03'], batchtable['neutralIsoPtSum'])
batchtable['neutralIsoPtSumdR03_over_dR05'] = safe_ratio(batchtable['neutralIsoPtSumdR03'], batchtable['neutralIsoPtSum'])
for ip in ['dxy', 'dz', 'ip3d']:
    batchtable['tau_%s_valid'%ip] = (batchtable['tau_%s'%ip] > - 10.) * (batchtable['tau_%s_error'%ip] > 0.)
    batchtable['tau_%s'%ip] *= batchtable['tau_%s_valid'%ip]
    batchtable['tau_%s_sig'%ip] = safe_ratio(np.abs(batchtable['tau_%s'%ip]), batchtable['tau_%s_error'%ip])
batchtable['tau_e_ratio_valid'] = batchtable['tau_e_ratio'] > 0.
batchtable['tau_e_ratio'] *= batchtable['tau_e_ratio_valid']
batchtable['tau_gj_angle_diff_valid'] = batchtable['tau_gj_angle_diff'] >= 0.
batchtable['tau_gj_angle_diff'] *= batchtable['tau_gj_angle_diff_valid']
batchtable['leadChargedCand_etaAtEcalEntrance_minus_tau_eta'] = batchtable['leadChargedCand_etaAtEcalEntrance'] - batchtable['tau_eta']

### creating (deta, dphi) grids; inner: 11 x 11 with size 0.02 x 0.02, outer: 21 x 21 with size 0.05 0.05
print(batchtable['muon_eta'])
print(batchtable['tau_eta'])
for q in ['eta', 'phi']:
    for p in ['ele', 'muon','pfCand']:
        batchtable['%s_d%s'%(p,q)] = batchtable['%s_%s'%(p,q)] - batchtable['tau_%s'%q]

print(batchtable[0]['pfCand_dphi'])
print(batchtable[0]['pfCand_deta'])

## transform quantities to [0, 1] interval
for name, interval in transformation_dict.items():
    batchtable[name] = transform_minmax(batchtable[name], interval[0], interval[1])

if plotting:
    h = plt.hist2d(batchtable[0]['pfCand_deta'], batchtable[0]['pfCand_dphi'], bins=[21,21], range=[[-0.525, 0.525], [-0.525, 0.525]])
    plt.xlabel('$\Delta\eta$')
    plt.ylabel('$\Delta\phi$')
    plt.colorbar(h[3])
    plt.title('N(PF candidates)')
    plt.savefig('pfCand_cell.png')
    plt.savefig('pfCand_cell.pdf')
print('finished')
