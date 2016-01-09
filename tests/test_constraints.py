#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test if constraints work with model functions.
"""
from __future__ import division, print_function

import sys
from os.path import abspath, dirname, split
import numpy as np
import os


# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import data_file_dl
import pycorrfit as pcf


def test_fit_constraint_simple_inequality():
    """ Check "smaller than" relation during fitting.
    """
    dfile = data_file_dl.get_data_file("019_cp_KIND+BFA.fcs")
    data = pcf.readfiles.openAny(dfile)
    corr = pcf.Correlation(correlation=data["Correlation"][0],
                           traces=data["Trace"][0],
                           corr_type=data["Type"][0],
                           filename=os.path.basename(dfile),
                           title="test correlation",
                           fit_model=6035 # confocal 3D+3D)
                           )
    corr.fit_parameters_variable = [True, True, True, True, False, False, False]
    # crop triplet data
    corr.fit_ival[0] = 8
    pcf.Fit(corr)
    assert corr.fit_parameters[1] <= corr.fit_parameters[2]
    # -> deliberately reverse everything and try again 
    corr.fit_parameters[1], corr.fit_parameters[2] = corr.fit_parameters[2], corr.fit_parameters[1]
    corr.fit_parameters[3] = 1-corr.fit_parameters[3]
    pcf.Fit(corr)
    # This tests also for equality
    assert corr.fit_parameters[1] <= corr.fit_parameters[2]
    if corr.fit_parameters[1] == corr.fit_parameters[2]:
        print("found identity of fit parameters - multiplying by two to see if relation holds")
        corr.fit_parameters[2] *= 2
        pcf.Fit(corr)
        assert corr.fit_parameters[1] < corr.fit_parameters[2]



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
