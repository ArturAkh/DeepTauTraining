import uproot
import uproot_methods
import glob
import awkward as ak
import numpy as np
import yaml
import matplotlib.pyplot as plt

plotting = False

flist = glob.glob('/ceph/akhmet/balanced_batches/batch0/*.root')
#flist = glob.glob('/ceph/akhmet/balanced_batches/batch0/*.root')[0:3]

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

def compute_placeindex(values, n_cells, cell_size):
    cone_size = n_cells * cell_size
    placeindex = ((values  + cone_size / 2.) * 100) // (cell_size * 100)
    placeindex = (placeindex >= 0) * (placeindex <= (n_cells - 1)) * placeindex - (placeindex < 0) - (placeindex > (n_cells - 1))
    return placeindex

def create_placematrix(deltaeta, deltaphi, n_cells):
    ones = deltaphi.ones_like()
    index_array = ones * 0.0
    deltaphi_place = deltaphi

    for i in np.arange(1,n_cells):
        index_array = index_array.zip(ones * i)
        deltaphi_place = deltaphi_place.zip(deltaphi)

    index_array = ak.fromiter(index_array.flattentuple().tolist())
    deltaphi_place = ak.fromiter(deltaphi_place.flattentuple().tolist())
    deltaphi_place = (index_array == deltaphi_place) * 1.0

    ones_array = deltaphi_place.ones_like()
    deltaeta_place_array = ones_array * deltaeta

    deltaeta_place_matrix = ((ones_array * 0.0) == deltaeta_place_array) * 1.0
    deltaphi_place_matrix = deltaphi_place

    for i in np.arange(1,n_cells):
        added = ((ones_array * i) == deltaeta_place_array) * 1.0
        deltaeta_place_matrix = deltaeta_place_matrix.zip(added)
        deltaphi_place_matrix = deltaphi_place_matrix.zip(deltaphi_place)

    deltaeta_place_matrix = ak.fromiter(deltaeta_place_matrix.flattentuple().tolist())
    deltaphi_place_matrix = ak.fromiter(deltaphi_place_matrix.flattentuple().tolist())

    placematrix = deltaeta_place_matrix * deltaphi_place_matrix
    return placematrix

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

for q in ['eta', 'phi']:
    for p in ['ele', 'muon','pfCand']:
        batchtable['%s_d%s'%(p,q)] = batchtable['%s_%s'%(p,q)] - batchtable['tau_%s'%q]
        batchtable['inner_%s_d%s_index'%(p,q)] = compute_placeindex(batchtable['%s_d%s'%(p,q)], n_inner_cells, inner_cell_size)
        batchtable['outer_%s_d%s_index'%(p,q)] = compute_placeindex(batchtable['%s_d%s'%(p,q)], n_outer_cells, outer_cell_size)

for p in ['ele', 'muon','pfCand']:
    batchtable['inner_%s_placematrix'%p] = create_placematrix(batchtable['inner_%s_deta_index'%p],batchtable['inner_%s_dphi_index'%p],n_inner_cells)
    batchtable['outer_%s_placematrix'%p] = create_placematrix(batchtable['outer_%s_deta_index'%p],batchtable['outer_%s_dphi_index'%p],n_outer_cells)

## transform quantities to [0, 1] interval
for name, interval in transformation_dict.items():
    batchtable[name] = transform_minmax(batchtable[name], interval[0], interval[1])

if plotting:
    h = plt.hist2d(batchtable[-1]['pfCand_deta'], batchtable[-1]['pfCand_dphi'], bins=[21,21], range=[[-0.525, 0.525], [-0.525, 0.525]])
    #h = plt.hist2d(batchtable[-1]['pfCand_deta'], batchtable[-1]['pfCand_dphi'], bins=[11,11], range=[[-0.11, 0.11], [-0.11, 0.11]])
    plt.xlabel('$\Delta\eta$')
    plt.ylabel('$\Delta\phi$')
    plt.colorbar(h[3])
    plt.title('N(PF candidates)')
    plt.savefig('pfCand_cell.png')
    plt.savefig('pfCand_cell.pdf')
print('finished')
