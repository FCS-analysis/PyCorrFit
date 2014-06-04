# -*- coding: utf-8 -*-
""" Wrapper for Loading PicoQuant .pt3 data files

    This function (in a very hackish way) wraps around classes and
    functions from FCS_viewer. Wrapping involves creating fake classes
    that usually are the graphical user interface.
    
    See Also:
    The wrapped file: `read_pt3_PicoQuant_original_FCSViewer.py`
    Fast implementation of dividAndConquer: `fib4.pyx`
"""
import numpy as np
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



wrapped.fname = "topfluorPE_2_1_1_1.pt3"
wrapped.corrObject = corrObject
wrapped.form = FakeMainObject()
wrapped.main = FakeMain()
po = wrapped.picoObject(wrapped.fname)

auto = po.autoNorm
# lag time [ms]
autotime = po.autotime

# autocorrelation CH0
# autotime,auto[:,0,0]

# autocorrelation CH1
# autotime,auto[:,1,1]

# Cross-Correlation CH0-CH1
# autotime,auto[:,0,1]

# Cross-Correlation CH1-CH0 ????
# autotime,auto[:,1,0]

import IPython
IPython.embed()







