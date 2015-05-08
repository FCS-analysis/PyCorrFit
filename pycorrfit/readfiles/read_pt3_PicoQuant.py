# -*- coding: utf-8 -*-
""" Wrapper for Loading PicoQuant .pt3 data files

Wraps around FCS_point_correlator by Dominic Waithe
https://github.com/dwaithe/FCS_point_correlator
"""
import numpy as np
import os
from .read_pt3_scripts.correlation_objects import picoObject


class ParameterClass():
    """Stores parameters for correlation """
    def __init__(self):
        #Where the data is stored.
        self.data = []
        self.objectRef =[]
        self.subObjectRef =[]
        self.colors = ['blue','green','red','cyan','magenta','yellow','black']
        self.numOfLoaded = 0
        self.NcascStart = 0
        self.NcascEnd = 25
        self.Nsub = 6
        self.winInt = 10
        self.photonCountBin = 25
        

def openPT3(dirname, filename):
    """ Retreive correlation curves from PicoQuant data files 
    
    This function is a wrapper around the PicoQuant capability of
    FCS_Viewer by Dominic Waithe.
    """
    par_obj = ParameterClass()
    
    pt3file = picoObject(os.path.join(dirname, filename), par_obj, None)

    po = pt3file

    auto = po.autoNorm
    # lag time [ms]
    autotime = po.autotime.reshape(-1)

    corrlist = list()
    typelist = list()
    
    # Some data points are zero for some reason
    id1 = np.where(autotime!=0)


    # AC0 - autocorrelation CH0
    corrac0 = auto[:,0,0]    
    if np.sum(np.abs(corrac0[id1])) != 0:
        typelist.append("AC0")
        # autotime,auto[:,0,0]
        corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                    corrac0[id1].reshape(-1,1)) ))
    
    # AC1 - autocorrelation CH1
    corrac1 = auto[:,1,1]
    if np.sum(np.abs(corrac1[id1])) != 0:
        typelist.append("AC1")
        # autotime,auto[:,1,1]
        corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                    corrac1[id1].reshape(-1,1)) ))
    
    # CC01 - Cross-Correlation CH0-CH1
    corrcc01 = auto[:,0,1]
    if np.sum(np.abs(corrcc01[id1])) != 0:
        typelist.append("CC01")
        # autotime,auto[:,0,1]
        corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                    corrcc01[id1].reshape(-1,1)) ))
    
    # CC10 - Cross-Correlation CH1-CH0
    corrcc10 = auto[:,1,0]
    if np.sum(np.abs(corrcc10[id1])) != 0:
        typelist.append("CC10")
        # autotime,auto[:,1,0]
        corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                    corrcc10[id1].reshape(-1,1)) ))


    filelist = [filename] * len(typelist)
    tracelist = [None] * len(typelist)

    dictionary = dict()
    dictionary["Correlation"] = corrlist
    dictionary["Trace"] = tracelist
    dictionary["Type"] = typelist
    dictionary["Filename"] = filelist

    return dictionary
