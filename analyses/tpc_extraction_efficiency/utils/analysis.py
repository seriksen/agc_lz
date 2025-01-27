from .store import Store
import awkward as ak
import uproot as up
import numpy as np
import dask

def create_output() -> Store:

    hist_dict = {}

    # Pulse the single scatter ones
    hist_dict['ss_s1_phd'] = ak.Array([])
    hist_dict['ss_s2_phd_raw'] = ak.Array([])
    hist_dict['ss_s2_phd_corrected'] = ak.Array([])
    hist_dict['ss_s2_phd_xy_corrected'] = ak.Array([])
    hist_dict['ss_s2_R'] = ak.Array([])
    hist_dict['ss_elife_correction'] = ak.Array([])
    hist_dict['ss_s2_elife_corrected'] = ak.Array([])
    hist_dict['peak_s2'] = ak.Array([])
    hist_dict['peak_s1'] = ak.Array([])
    hist_dict['peak_r'] = ak.Array([])

    return Store(hist_dict)


@dask.delayed
def single_file_analysis(file: str, output: Store) -> Store:
    tfile = up.open(file)
    scatters = tfile['Scatters']
    events = tfile['Events']

    # Single Scatter cut
    is_ss = np.where(scatters['ss./ss.nSingleScatters'].array() == 1)


    s1_phd = scatters['ss./ss.s1Area_phd'].array()[is_ss].to_numpy()
    s2_phd_raw = scatters['ss./ss.s2Area_phd'].array()[is_ss].to_numpy()
    s2_phd_corrected = scatters['ss./ss.correctedS2Area_phd'].array()[is_ss].to_numpy()
    s2_phd_xy_corrected = scatters['ss./ss.xyCorrectedS2Area_phd'].array()[is_ss].to_numpy()
    s2_x = scatters['ss./ss.correctedX_cm'].array()[is_ss].to_numpy()
    s2_y = scatters['ss./ss.correctedY_cm'].array()[is_ss].to_numpy()
    s2_r = np.sqrt(s2_x ** 2 + s2_y ** 2)

    # apply correction factor
    elife_correction = s2_phd_corrected / s2_phd_xy_corrected
    s2_phd_elife_corrected = s2_phd_raw * elife_correction


    output['s1_phd'] = s1_phd
    output['s2_phd_raw'] = s2_phd_raw
    output['s2_phd_corrected'] = s2_phd_corrected
    output['s2_phd_xy_corrected'] = s2_phd_xy_corrected
    output['s2_R'] = s2_r
    output['elife_correction'] = elife_correction
    output['s2_phd_elife_corrected'] = s2_phd_elife_corrected


    # Apply box cut
    final_selection = np.array(np.log10(s2_phd_elife_corrected) <= 5.0) \
                * np.array(np.log10(s2_phd_elife_corrected) >= 4.0) \
                * np.array(s1_phd >= 150) \
                * np.array(s1_phd <= 400)
    
    peak_s2 = s2_phd_elife_corrected[final_selection]
    peak_s1 = s1_phd[final_selection]
    peak_r = s2_r[final_selection]

    output['peak_s2'] = peak_s2
    output['peak_s1'] = peak_s1
    output['peak_r'] = peak_r

    output.completed = True
    return output
