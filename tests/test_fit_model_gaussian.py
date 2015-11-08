#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Go through each model, vary one parameter and fit it back to the
default value of that model.
"""
from __future__ import division, print_function
import sys
from os.path import abspath, dirname, split

import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))

import pycorrfit
from pycorrfit import models as mdls

# GLOBAL PARAMETERS FOR THIS TEST:
TAU = 1.468e-6
FITALG = "Lev-Mar"


def test_6001():
    #2D
    model = mdls.modeldict[6001]
    parms = [4.874, 0.2476, 0.015]
    assert model(parms, tau=TAU) == 0.22016907491127263


def test_6002():
    #T+2D
    model = mdls.modeldict[6002]
    parms = [4.891, 0.853, 0.00141, 0.0121, 0.034]
    assert model(parms, tau=TAU) == 0.24095843709396209
    
    model2 = mdls.modeldict[6001]
    parms2 = [4.891, 0.853, 0.034]
    parms1 = [4.891, 0.853, 0.0, 0.0, 0.034]
    assert model(parms1, tau=TAU) == model2(parms2, tau=TAU)
    

def test_6031():
    #T+2D+2D
    model = mdls.modeldict[6031]
    parms = [ 
                2.487,        # n
                3.4325,      # taud1
                2534,        # taud2
                0.153,       # F
                .879,        # alpha
                0.00123,     # tautrip
                0.0314,      # T
                0.00021      # offset
                ]
    assert model(parms, tau=TAU) == 0.41629799102222742
    
    model2 = mdls.modeldict[6002]
    parms2 = [4.891, 0.853, 0.0012, 0.108, 0.034]
    parms1 = [ 
                4.891,      # n
                0.853,      # taud1
                1.0,        # taud2
                1.0,        # F
                1.0,        # alpha
                0.0012,     # tautrip
                0.108,      # T
                0.034       # offset
                ]
    assert  model(parms1, tau=TAU) == model2(parms2, tau=TAU)


def test_6011():
    #T+3D
    model = mdls.modeldict[6011]
    # n T τ_trip τ_diff SP offset
    parms = [2.168, 0.1682, 0.00028, 0.54, 5.864, 0.0053]
    assert model(parms, tau=TAU) == 0.55933660640533278

    model2 = mdls.modeldict[6012]
    parms2 = [2.168, 0.54, 5.864, 0.0053]
    parms1 = [2.168, 0, 1.0, 0.54, 5.864, 0.0053]
    assert  model(parms1, tau=TAU) == model2(parms2, tau=TAU)


def test_6012():
    #3D
    model = mdls.modeldict[6012]
    parms = [2.168, 0.54, 5.864, 0.0053]
    assert model(parms, tau=TAU) == 0.46655334038750634


def test_6030():
    #T+3D+3D
    model = mdls.modeldict[6030]
    parms = [ 
                2.153,      # n
                5.54,       # taud1
                1532,       # taud2
                0.4321,     # F
                4.4387,     # SP
                0.9234,     # alpha
                0.002648,   # tautrip
                0.1151,     # T
                0.008       # offset
                ]
    assert model(parms, tau=TAU) == 0.53367456244118261
    
    model2 = mdls.modeldict[6011]
    #             n       T   τ_trip τ_diff    SP  offset
    parms2 = [2.168, 0.1682, 0.00028, 0.54, 5.864, 0.0053]
    parms1 = [ 
                2.168,       # n
                0.54,        # taud1
                1.0,         # taud2
                1.0,         # F
                5.864,       # SP
                0.9234,      # alpha
                0.00028,     # tautrip
                0.1682,      # T
                0.0053       # offset
                ]
    assert  model(parms1, tau=TAU) == model2(parms2, tau=TAU)
    


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()

    
    