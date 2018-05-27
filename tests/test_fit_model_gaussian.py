"""Check known model parameters and cross-check across models"""

from os.path import abspath, dirname, split
import sys

import numpy as np

import pycorrfit
from pycorrfit import models as mdls

# GLOBAL PARAMETERS FOR THIS TEST:
TAU = 1.468e-6


def test_6001():
    # 2D
    model = mdls.modeldict[6001]
    parms = [4.874, 0.2476, 0.015]
    assert abs(model(parms, tau=TAU) - 0.22016907491127263) < 1e-14


def test_6002():
    # T+2D
    model = mdls.modeldict[6002]
    #         n     τ_diff τ_trip     T     offset
    parms = [4.891, 0.853, 0.00141, 0.0121, 0.034]
    assert abs(model(parms, tau=TAU) - 0.24095843709396209) < 1e-14

    model2 = mdls.modeldict[6001]
    parms2 = [4.891, 0.853, 0.034]
    parms1 = [4.891, 0.853, 0.0, 0.0, 0.034]
    assert abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6031():
    # T+2D+2D
    model = mdls.modeldict[6031]
    parms = [2.487,    # n
             3.4325,   # taud1
             2534,     # taud2
             0.153,    # F
             0.879,    # alpha
             0.00123,  # tautrip
             0.0314,   # T
             0.00021]  # offset
    assert abs(model(parms, tau=TAU) - 0.41629799102222742) < 1e-14

    model2 = mdls.modeldict[6002]
    parms2 = [4.891, 0.853, 0.0012, 0.108, 0.034]
    parms1 = [4.891,      # n
              0.853,      # taud1
              1.0,        # taud2
              1.0,        # F
              1.0,        # alpha
              0.0012,     # tautrip
              0.108,      # T
              0.034]      # offset
    assert abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6011():
    # T+3D
    model = mdls.modeldict[6011]
    #            n       T   τ_trip τ_diff    SP  offset
    parms = [2.168, 0.1682, 0.00028, 0.54, 5.864, 0.0053]
    assert abs(model(parms, tau=TAU) - 0.55933660640533278) < 1e-14

    model2 = mdls.modeldict[6012]
    parms2 = [2.168, 0.54, 5.864, 0.0053]
    parms1 = [2.168, 0, 1.0, 0.54, 5.864, 0.0053]
    assert abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6012():
    # 3D
    model = mdls.modeldict[6012]
    parms = [2.168, 0.54, 5.864, 0.0053]
    assert abs(model(parms, tau=TAU) - 0.46655334038750634) < 1e-14


def test_6030():
    # T+3D+3D
    model = mdls.modeldict[6030]
    parms = [2.153,      # n
             5.54,       # taud1
             1532,       # taud2
             0.4321,     # F
             4.4387,     # SP
             0.9234,     # alpha
             0.002648,   # tautrip
             0.1151,     # T
             0.008]      # offset
    assert abs(model(parms, tau=TAU) - 0.53367456244118261) < 1e-14

    model2 = mdls.modeldict[6011]
    #             n       T   τ_trip τ_diff    SP  offset
    parms2 = [2.168, 0.1682, 0.00028, 0.54, 5.864, 0.0053]
    parms1 = [2.168,       # n
              0.54,        # taud1
              1.0,         # taud2
              1.0,         # F
              5.864,       # SP
              0.9234,      # alpha
              0.00028,     # tautrip
              0.1682,      # T
              0.0053]      # offset
    assert  abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6032():
    #T+3D+2D
    model = mdls.modeldict[6032]
    parms = [1.58,      # n
             3548,      # taud2D
             0.351,     # taud3D
             0.345,     # F3D
             4.984,     # SP
             0.879,     # alpha
             0.0014,    # tautrip
             0.108,     # T
             0.008]     # offset
    assert abs(model(parms, tau=TAU) - 0.72001694812574801) < 1e-14

    # ->T+3D
    model2 = mdls.modeldict[6011]
    #             n       T   τ_trip τ_diff    SP  offset
    parms2 = [2.168, 0.1682, 0.0028, 0.54, 5.864, 0.0053]
    parms1a = [2.168,      # n
               1.0,        # taud2D
               0.54,       # taud3D
               1.0,        # F3D
               5.864,      # SP
               0.879,      # alpha
               0.0028,     # tautrip
               0.1682,     # T
               0.0053]     # offset
    assert abs(model(parms1a, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14

    # ->T+2D
    model3 = mdls.modeldict[6002]
    #         n     τ_diff τ_trip     T     offset
    parms3 = [4.891, 0.853, 0.00141, 0.0121, 0.034]
    parms1b = [4.891,    # n
               0.853,    # taud2D
               1.0,      # taud3D
               0.0,      # F3D
               1.0,      # SP
               0.879,    # alpha
               0.00141,  # tautrip
               0.0121,   # T
               0.034]    # offset
    assert abs(model(parms1b, tau=TAU) - model3(parms3, tau=TAU)) < 1e-14


def test_6043():
    # TT+3D+3D
    model = mdls.modeldict[6043]
    parms = [1.452,       # n
             4.48,        # taud1
             8438,        # taud2
             0.425,       # F
             5.43,        # SP
             0.876,       # alpha
             0.0012,      # tautrip1
             0.0101,      # T1
             0.0021,      # tautrip2
             0.0102,      # T2
             0.00004]     # offset
    assert abs(model(parms, tau=TAU) - 0.70599013426715551) < 1e-14

    # ->T+3D+3D
    model2 = mdls.modeldict[6030]
    parms2 = [2.153,      # n
              5.54,       # taud1
              1532,       # taud2
              0.4321,     # F
              4.4387,     # SP
              0.9234,     # alpha
              0.002648,   # tautrip
              0.1151,     # T
              0.008]      # offset
    parms1 = [2.153,      # n
              5.54,       # taud1
              1532,       # taud2
              0.4321,     # F
              4.4387,     # SP
              0.9234,     # alpha
              0.002648,   # tautrip1
              0.1151,     # T1
              0.0021,     # tautrip2
              0.0,        # T2
              0.008]      # offset

    assert abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6044():
    # TT+2D+2D
    model = mdls.modeldict[6044]
    parms = [1.452,       # n
             4.48,        # taud1
             8438,        # taud2
             0.425,       # F
             0.876,       # alpha
             0.0012,      # tautrip1
             0.0101,      # T1
             0.0021,      # tautrip2
             0.0102,      # T2
             0.00004]     # offset
    assert abs(model(parms, tau=TAU) - 0.70599013619282502) < 1e-14

    # ->T+2D+2D
    model2 = mdls.modeldict[6031]
    parms2 = [2.153,      # n
              5.54,       # taud1
              1532,       # taud2
              0.4321,     # F
              0.9234,     # alpha
              0.002648,   # tautrip
              0.1151,     # T
              0.008]      # offset
    parms1 = [2.153,      # n
              5.54,       # taud1
              1532,       # taud2
              0.4321,     # F
              0.9234,     # alpha
              0.002648,   # tautrip1
              0.1151,     # T1
              0.0021,     # tautrip2
              0.0,        # T2
              0.008]      # offset

    assert abs(model(parms1, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6045():
    # TT+3D+2D
    model = mdls.modeldict[6045]
    parms = [25.123,      # n
             240.123,     # taud2D
             0.1125,      # taud3D
             0.3512,      # F3D
             5.312,       # SP
             0.87671,     # alpha
             0.0021987,   # tautrip1
             0.032341,    # T1
             0.0013243,   # tautrip2
             0.014341,    # T2
             0.12310]     # offset
    assert abs(model(parms, tau=TAU) - 0.16498917764250026) < 1e-14

    # ->T+3D+2D
    model2 = mdls.modeldict[6032]
    parms2 = [25.123,      # n
              240.123,     # taud2D
              0.1125,      # taud3D
              0.3512,      # F3D
              5.312,       # SP
              0.87671,     # alpha
              0.0021987,   # tautrip1
              0.032341,    # T1
              0.12310]     # offset

    parms1a = [25.123,      # n
               240.123,     # taud2D
               0.1125,      # taud3D
               0.3512,      # F3D
               5.312,       # SP
               0.87671,     # alpha
               0.0021987,   # tautrip1
               0.032341,    # T1
               0.1,   # tautrip2
               0.0,    # T2
               0.12310]     # offset
    parms1b = [25.123,      # n
               240.123,     # taud2D
               0.1125,      # taud3D
               0.3512,      # F3D
               5.312,       # SP
               0.87671,     # alpha
               0.1,   # tautrip1
               0.0,    # T1
               0.0021987,   # tautrip2
               0.032341,    # T2
               0.12310]     # offset
    assert abs(model(parms1a, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14
    assert abs(model(parms1b, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6081():
    # T+3D+3D+3D
    model = mdls.modeldict[6081]
    parms = [1.412,       # n
             4.498,       # taud1
             245,         # taud2
             2910,        # taud3
             0.123,       # F1
             0.321,       # F3
             5.12,        # SP
             0.876,       # alpha21
             0.378,       # alpha31
             0.0021,      # tautrip
             0.021,       # T
             -0.0004]     # offset
    assert abs(model(parms, tau=TAU) - 0.85970140411643392) < 1e-14

    # ->T+3D+3D
    model2 = mdls.modeldict[6030]
    parms2 = [2.153,      # n
              1.120,      # taud1
              30.120,     # taud2
              0.4321,     # F
              4.4387,     # SP
              0.4321,     # alpha
              0.002,      # tautrip
              0.1151,     # T
              1.2008]     # offset

    parmsa = [2.153,      # n
              1.120,      # taud1
              30.120,     # taud2
              100.00,     # taud3
              0.4321,     # F1
              1-0.4321,   # F2
              4.4387,     # SP
              0.4321,     # alpha21
              1,          # alpha31
              0.002,      # tautrip
              0.1151,     # T
              1.2008]     # offset

    parmsb = [2.153,      # n
              1.120,      # taud1
              10.000,     # taud2
              30.120,     # taud3
              0.4321,     # F1
              0,          # F2
              4.4387,     # SP
              1,          # alpha21
              .4321,      # alpha31
              0.002,      # tautrip
              0.1151,     # T
              1.2008]     # offset

    assert abs(model(parmsa, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14
    assert abs(model(parmsb, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


def test_6082():
    # T+3D+3D+2D
    model = mdls.modeldict[6082]
    parms = [1.412,       # n
             4.498,       # taud1
             245,         # taud2
             2910,        # taud3
             0.123,       # F1
             0.321,       # F3
             5.12,        # SP
             0.876,       # alpha21
             0.378,       # alpha31
             0.0021,      # tautrip
             0.021,       # T
             -0.0004]     # offset
    assert abs(model(parms, tau=TAU) - 0.85970140411789908) < 1e-14

    # ->T+3D+2D
    model2 = mdls.modeldict[6032]
    parms2 = [2.153,      # n
              30.120,     # taud1
              1.234,      # taud2
              0.4321,     # F
              4.4387,     # SP
              1.341,      # alpha
              0.002,      # tautrip
              0.1151,     # T
              1.2008]     # offset

    parmsa = [2.153,      # n
              1.234,      # taud1
              1,      # taud2
              30.120,     # taud3
              0.4321,     # F1
              0,      # F2
              4.4387,     # SP
              1.,         # alpha21
              1/1.341,    # alpha31
              0.002,      # tautrip
              0.1151,     # T
              1.2008]      # offset

    parmsb = [2.153,      # n
              1,      # taud1
              1.234,      # taud2
              30.120,     # taud3
              0,      # F1
              0.4321,     # F2
              4.4387,     # SP
              1,          # alpha21
              1/1.341,    # alpha31
              0.002,      # tautrip
              0.1151,     # T
              1.2008]     # offset

    assert abs(model(parmsa, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14
    assert abs(model(parmsb, tau=TAU) - model2(parms2, tau=TAU)) < 1e-14


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
