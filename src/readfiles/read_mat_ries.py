# -*- coding: utf-8 -*-
"""
Read mat files that Jonas Ries used in his programs.
For opening .mat files, this helped a lot:
http://stackoverflow.com/questions/7008608/
scipy-io-loadmat-nested-structures-i-e-dictionaries

The structure has been derived from "corrSFCS.m" from the SFCS.m program
from Jonas Ries.
"""

import csv
import numpy as np

# On the windows machine the matlab binary import raised a warning.
# We want to catch that warning, since importing ries's files works.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import scipy.io as spio
    import scipy.io.matlab
    try:
        # streams is not available in older versions
        # of scipy. We catch this, so PyCorrFit will start
        # without problems.
        import scipy.io.matlab.streams
    except:
        print " Error: scipy.io.matlab.streams not found!"
        print "        Try upgrading python-scipy."
import os


def openMAT(dirname, filename):
    # initiate lists
    correlations = list()
    traces = list()
    curvelist = list()
    # Import everything inside the mat file as big iterated dictionary
    f = os.path.join(dirname, filename)
    alldata = loadmat(f)
    # Correlation functions are stored in "g"
    g = alldata["g"]
    # Get all Autocorrelation functions
    try:
        # ac for autocorrelation
        ac = g["ac"]
    except KeyError:
        pass
    else:
        N = len(ac)
        # Workaround for single ACs, they are not stored in a separate list,
        # but directly inserted into g["ac"]. We put it in a list.
        # This is not the case for the trace averages.
        # There are a maximum of 4 autocorrelation functions in one file,
        # as far as I know.
        if len(ac) > 4:
            N=1
            ac = [ac]
            g["act"] = [g["act"]]
        for i in np.arange(len(ac)):
            corr = ac[i]
            try:
                times = g["act"][i]
            except KeyError:
                pass
            else:
                # Another workaround
                # Sometimes, there's just one curve, which
                # means that corr[0] has no length.
                if len( np.atleast_1d(corr[0]) ) == 1:
                    final = np.zeros((len(corr), 2))
                    final[:,0] = times
                    final[:,1] = corr
                    correlations.append(final)
                    curvelist.append("AC"+str(i+1))
                    try:
                        # only trace averages are saved
                        traceavg = g["trace"][i][j]
                    except:
                        # No trace
                        traces.append(None)
                    else:
                        trace = np.zeros((2,2))
                        trace[1,0] = 1.0
                        trace[:,1] = traceavg
                        traces.append(trace)


                elif len(corr) == len(times):
                    for j in np.arange(len(corr[0])):

                        final = np.zeros((len(corr), 2))
                        final[:,0] = times
                        final[:,1] = corr[:,j]
                        correlations.append(final)
                        curvelist.append("AC"+str(i+1))
                        try:
                            # only trace averages are saved
                            traceavg = g["trace"][i][j]
                        except:
                            # No trace
                            traces.append(None)
                        else:
                            trace = np.zeros((2,2))
                            trace[1,0] = 1.0
                            trace[:,1] = traceavg
                            traces.append(trace)
    # Get dc "dual color" functions
    try:
        dc = g["dc"]
    except KeyError:
        pass
    else:
        for i in np.arange(len(dc)):
            corr = dc[i]
            try:
                times = g["dct"][i]
            except KeyError:
                pass
            else:
                if len(corr) == len(times):
                    for j in np.arange(len(corr[0])):

                        final = np.zeros((len(corr), 2))
                        final[:,0] = times
                        final[:,1] = corr[:,j]
                        correlations.append(final)
                        curvelist.append("CC dual color "+str(i+1))
                        traces.append(None)
    # Get twof "two focus" functions
    try:
        twof = g["twof"]
    except KeyError:
        pass
    else:
        for i in np.arange(len(dc)):
            corr = twof[i]
            try:
                times = g["twoft"][i]
            except KeyError:
                pass
            else:
                if len(corr) == len(times):
                    for j in np.arange(len(corr[0])):

                        final = np.zeros((len(corr), 2))
                        final[:,0] = times
                        final[:,1] = corr[:,j]
                        correlations.append(final)
                        curvelist.append("CC two foci "+str(i+1))
                        traces.append(None)
    # Get dc2f "dual color two focus" functions
    try:
        dc2f = g["dc2f"]
    except KeyError:
        pass
    else:
        for i in np.arange(len(dc)):
            corr = twof[i]
            try:
                times = g["dc2ft"][i]
            except KeyError:
                pass
            else:
                if len(corr) == len(times):
                    for j in np.arange(len(corr[0])):

                        final = np.zeros((len(corr), 2))
                        final[:,0] = times
                        final[:,1] = corr[:,j]
                        correlations.append(final)
                        curvelist.append("CC dual color two foci "+str(i+1))
                        traces.append(None)
    dictionary = dict()
    dictionary["Correlation"] = correlations
    dictionary["Trace"] = traces
    dictionary["Type"] = curvelist
    filelist = list()
    for i in curvelist:
        filelist.append(filename)
    dictionary["Filename"] = filelist
    return dictionary


def loadmat(filename):
    '''
    this function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    '''
    data = spio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)


def _check_keys(dict):
    '''
    checks if entries in dictionary are mat-objects. If yes
    todict is called to change them to nested dictionaries
    '''
    for key in dict:
        if isinstance(dict[key], spio.matlab.mio5_params.mat_struct):
            dict[key] = _todict(dict[key])
    return dict        

def _todict(matobj):
    '''
    A recursive function which constructs from matobjects nested dictionaries
    '''
    dict = {}
    for strg in matobj._fieldnames:
        elem = matobj.__dict__[strg]
        if isinstance(elem, spio.matlab.mio5_params.mat_struct):
            dict[strg] = _todict(elem)
        else:
            dict[strg] = elem
    return dict
