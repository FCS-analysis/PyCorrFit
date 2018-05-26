"""Session files"""
import os
import pathlib
import tempfile
import shutil

import numpy as np
import pytest

import data_file_dl
import pycorrfit as pcf

NOAPITOKEN = "GITHUB_API_TOKEN" not in os.environ

examplefile = "Zeiss_Confocor3_LSM780_FCCS_HeLa_2015/019_cp_KIND+BFA.fcs"


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_basic():
    """This is a very rudimentary test for the session handling"""
    dfile = data_file_dl.get_data_file(examplefile)
    data = pcf.readfiles.openAny(dfile)
    corr = pcf.Correlation(correlation=data["Correlation"][0],
                           traces=data["Trace"][0],
                           corr_type=data["Type"][0],
                           filename=os.path.basename(dfile),
                           title="test correlation",
                           fit_model=6035  # confocal 3D+3D)
                           )
    corr.fit_parameters_variable = [True, True, True, True,
                                    False, False, False]
    # crop triplet data
    corr.fit_ival[0] = 8
    pcf.Fit(corr)
    
    tmpdir = tempfile.mkdtemp(prefix="pycorrfit_tests_")
    path = pathlib.Path(tmpdir) / "session.pcfs"

    fiterr = []
    for ii, fitpid in enumerate(corr.fit_results["fit parameters"]):
        fiterr.append([int(fitpid),
                       float(corr.fit_results["fit error estimation"][ii])])

    Infodict = {
        "Correlations": {
            1: [corr.lag_time, corr.correlation]},
        "Parameters": {
            1: ["#1:",
                corr.fit_model.id,
                corr.fit_parameters,
                corr.fit_parameters_variable,
                corr.fit_ival,
                [3, 3, 5, corr.fit_algorithm],
                [None, None],
                True,
                None,
                [[0.0, np.inf],
                 [0.0, np.inf],
                 [0.0, np.inf],
                 [0.0, 0.9999999999999],
                 [-np.inf, np.inf]]
                ]},
        "Supplements": {
            1: {"FitErr": fiterr,
                "Chi sq": float(corr.fit_results["chi2"]),
                "Global Share": [],
            }},
        "External Functions": {},
        "Traces": {},
        "Comments": {"Session": "No comment."},
        "Backgrounds": {},
        "External Weights": {},
        "Preferences": {},
        }
    
    pcf.openfile.SaveSessionData(sessionfile=str(path),
                                 Infodict=Infodict)
    
    ldt = pcf.openfile.LoadSessionData(str(path))
    
    # lag time only, shape (N,)
    assert np.allclose(data["Correlation"][0][:,0], ldt["Correlations"][1][0])
    # lag time and correlation, shape (N, 2)
    assert np.allclose(corr.correlation, ldt["Correlations"][1][1])
    # parameters
    assert corr.fit_model.id == ldt["Parameters"][0][1]
    assert np.allclose(corr.fit_parameters, ldt["Parameters"][0][2])
    assert np.allclose(corr.fit_parameters_variable, ldt["Parameters"][0][3])
    assert np.allclose(corr.fit_ival, ldt["Parameters"][0][4])
    
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
