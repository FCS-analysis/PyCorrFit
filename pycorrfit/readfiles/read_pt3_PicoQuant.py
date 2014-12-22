# -*- coding: utf-8 -*-
""" Wrapper for Loading PicoQuant .pt3 data files

This function (in a very hackish way) wraps around classes and
functions from FCS_viewer. Wrapping involves creating fake classes
that usually are the graphical user interface.

See Also:
The wrapped file: `read_pt3_PicoQuant_original_FCSViewer.py`
Fast implementation of dividAndConquer: `read_pt3_PicoQuant_fib4.pyx`
"""
import numpy as np
import os
import read_pt3_PicoQuant_original_FCSViewer as wrapped


class FakeMainObject2():
    def __init__(self, value=None):
        self.name = " "
        self.autoNorm = None
        self.autotime = None
        self.param = None
        
    def updateFitList(self):
        pass
        
class FakeMainObject():
    def __init__(self, value=None):
        self.value = value
        self.numOfLoaded = 0
        self.objId = FakeMainObject2()
        self.objIdArr = list()
        self.name = " "
        self.def_param = 0

    def text(self):
        return self.value

    def generateList(self):
        pass
        
    def setCurrentIndex(self, *args):
        pass

    def fill_series_list(self, *args):
        pass


class corrObject(FakeMainObject):
    def __init__(self, *args):
        FakeMainObject.__init__(self)
    pass


class FakeMain():
    def __init__(self):
        self.data = list()
        self.objectRef = list()
        self.label = FakeMainObject()
        self.TGScrollBoxObj = FakeMainObject()
        self.cbx = FakeMainObject()
        
        self.NcascStartEdit = FakeMainObject(0)
        self.NcascEndEdit = FakeMainObject(25)
        self.NsubEdit = FakeMainObject(6)
        self.winIntEdit = FakeMainObject(10)
        self.photonCountEdit = FakeMainObject(25)
        
        self.colors = self.colors = ['blue','green','red','cyan']

        self.name = " "


    def updateCombo(self, e=None):
        pass
    
    def plot_PhotonCount(self, e=None):
        pass


def openPT3(dirname, filename):
    """ Retreive correlation curves from PicoQuant data files 
    
    This function is a wrapper around the PicoQuant capability of
    FCS_Viewer by Dominic Waithe.
    """

    wrapped.fname = os.path.join(dirname, filename)
    wrapped.corrObject = corrObject
    wrapped.form = FakeMainObject()
    wrapped.main = FakeMain()
    po = wrapped.picoObject(wrapped.fname)

    auto = po.autoNorm
    # lag time [ms]
    autotime = po.autotime.reshape(-1)

    corrlist = list()
    tracelist = list()
    typelist = list()
    
    # Some data points are zero for some reason
    id1 = np.where(autotime!=0)

    
    # AC0 - autocorrelation CH0
    typelist.append("AC0")
    # autotime,auto[:,0,0]
    corrac0 = auto[:,0,0]
    corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                corrac0[id1].reshape(-1,1)) ))

    # AC1 - autocorrelation CH1
    typelist.append("AC1")
    # autotime,auto[:,1,1]
    corrac1 = auto[:,1,1]
    corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                corrac1[id1].reshape(-1,1)) ))

    # CC01 - Cross-Correlation CH0-CH1
    typelist.append("CC01")
    # autotime,auto[:,0,1]
    corrcc01 = auto[:,0,1]
    corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                corrcc01[id1].reshape(-1,1)) ))
    
    # CC10 - Cross-Correlation CH1-CH0
    typelist.append("CC10")
    # autotime,auto[:,1,0]
    corrcc10 = auto[:,1,0]
    corrlist.append(np.hstack( (autotime[id1].reshape(-1,1),
                                corrcc10[id1].reshape(-1,1)) ))

    dictionary = dict()
    dictionary["Correlation"] = corrlist
    dictionary["Trace"] = tracelist
    dictionary["Type"] = typelist
    filelist = list()
    for i in typelist:
        filelist.append(filename)
        tracelist.append(None)
    dictionary["Filename"] = filelist
    
    return dictionary
