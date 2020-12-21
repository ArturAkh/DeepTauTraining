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

n_pop_events = 2
tables = {}

def transform_minmax(values, minval, maxval):
    return (np.clip(values, minval, maxval) - minval)/(maxval - minval)

def safe_ratio(numerator, denominator):
    nonnull_denominator = denominator != 0.
    denominator = denominator * nonnull_denominator + np.invert(nonnull_denominator)
    numerator *= nonnull_denominator
    return numerator / denominator


def create_placematrix(deltaeta, deltaphi, n_cells, cell_size):
    placematrix = None
    return placematrix

def compute_placeindex(values, n_cells, cell_size):
    cone_size = n_cells * cell_size
    placeindex = ((values  + cone_size / 2.) * 100) // (cell_size * 100)
    placeindex = (placeindex >= 0) * (placeindex <= (n_cells - 1)) * placeindex - (placeindex < 0) - (placeindex > (n_cells - 1))
    return placeindex

for f in flist:
    print(f)
    with uproot.open(f) as F:
        tables[f] = ak.Table(F['taus'].arrays(namedecode='utf-8'))

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
inner_cell_size = 0.02
n_inner_cells = 11
outer_cell_size = 0.05
n_outer_cells = 21


#TODO: make fuction for index creation, perhaps even hide in the place_matrix function
for q in ['eta', 'phi']:
    for p in ['ele', 'muon','pfCand']:
        batchtable['%s_d%s'%(p,q)] = batchtable['%s_%s'%(p,q)] - batchtable['tau_%s'%q]
        batchtable['inner_%s_d%s_index'%(p,q)] = compute_placeindex(batchtable['%s_d%s'%(p,q)], n_inner_cells, inner_cell_size)
        batchtable['outer_%s_d%s_index'%(p,q)] = compute_placeindex(batchtable['%s_d%s'%(p,q)], n_outer_cells, outer_cell_size)

#TODO get place matrix via trick:
'''
place = (7, 5)
index_eta = np.arange(0, 12)
index_phi = np.arange(0, 12)
place_eta = np.where(index_eta == place[0], 1, 0)
place_phi = np.where(index_phi == place[1], 1, 0)
place_matrix = np.tensordot(place_eta,place_phi, axes=0)

place_matrix[7][5] # ---> 1 as needed
'''

print(batchtable[-1]['pfCand_deta'])
print(batchtable[-1]['inner_pfCand_deta_index'])
print(batchtable[-1]['outer_pfCand_deta_index'])
print(len(batchtable[-1]['pfCand_dphi']))
print(np.sum((batchtable[-1]['inner_pfCand_deta_index'] >= 0.0) * (batchtable[-1]['inner_pfCand_dphi_index'] >= 0.0) ))

## transform quantities to [0, 1] interval
for name, interval in transformation_dict.items():
    batchtable[name] = transform_minmax(batchtable[name], interval[0], interval[1])

if plotting:
    #h = plt.hist2d(batchtable[-1]['pfCand_deta'], batchtable[-1]['pfCand_dphi'], bins=[21,21], range=[[-0.525, 0.525], [-0.525, 0.525]])
    h = plt.hist2d(batchtable[-1]['pfCand_deta'], batchtable[-1]['pfCand_dphi'], bins=[11,11], range=[[-0.11, 0.11], [-0.11, 0.11]])
    plt.xlabel('$\Delta\eta$')
    plt.ylabel('$\Delta\phi$')
    plt.colorbar(h[3])
    plt.title('N(PF candidates)')
    plt.savefig('pfCand_cell.png')
    plt.savefig('pfCand_cell.pdf')
print('finished')
