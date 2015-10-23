# -*- coding: utf-8 -*-
"""
utility functions for reading data
"""
from __future__ import division

import numpy as np

def downsample_trace(trace, bestlength=500):
    """
    Reduces the length of a trace so that there is no undersampling on a
    regular computer screen and the data size is not too large.
    
    Downsampling is performed by averaging neighboring intensity values
    for two time bins and omitting the first time bin.
    """
    # The trace is too big. Wee need to bin it.
    if len(trace) >= bestlength:
        # We want about 500 bins
        # We need to sum over intervals of length *teiler*
        teiler = int(np.floor(len(trace)/bestlength))
        newlength = int(np.floor(len(trace)/teiler))
        newsignal = np.zeros(newlength)
        # Simultaneously sum over all intervals
        for j in np.arange(teiler):
            newsignal = \
                 newsignal+trace[j:newlength*teiler:teiler][:,1]
        newsignal = 1.* newsignal / teiler
        newtimes = trace[teiler-1:newlength*teiler:teiler][:,0]
        if len(trace)%teiler != 0:
            # We have a rest signal
            # We average it and add it to the trace
            rest = trace[newlength*teiler:][:,1]
            lrest = len(rest)
            rest = np.array([sum(rest)/lrest])
            newsignal = np.concatenate((newsignal, rest),
                                       axis=0)
            timerest = np.array([trace[-1][0]])
            newtimes = np.concatenate((newtimes, timerest),
                                      axis=0)
        newtrace=np.zeros((len(newtimes),2))
        newtrace[:,0] = newtimes
        newtrace[:,1] = newsignal
    else:
        # Declare newtrace -
        # otherwise we have a problem down three lines ;)
        newtrace = trace
    return newtrace