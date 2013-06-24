# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools
    This file contains useful tools, such as dialog boxes and other stuff,
    that we need in PyCorrFit.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


# This file is necessary for this folder to become a module that can be 
# imported by PyCorrFit or other people.

import importlib
import numpy as np                  # NumPy
import sys

## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
reload(sys)
sys.setdefaultencoding('utf-8')

import channels
import background
import selectcurves
import batch
import globalfit
import average
import simulation

import info
import statistics
import trace
# Load all of the classes
# This also defines the order of the tools in the menu
ImpA = [ 
        ["channels", "SelectChannels"],
        ["background", "BackgroundCorrection"],
        ["selectcurves", "Wrapper_Tools"],
        ["batch", "BatchCtrl"],
        ["globalfit", "GlobalFit"],
        ["average", "Average"],
        ["simulation", "Slide"]
       ]

ImpB = [
        ["info", "ShowInfo"],
        ["statistics", "Stat"],
        ["trace", "ShowTrace"]
       ]

ModuleActive = list()
ToolsActive = list()
for i in np.arange(len(ImpA)):
    # We have to add "tools." because this is a relative import
    ModuleActive.append(__import__(ImpA[i][0], globals(), locals(), [ImpA[i][1]], -1))
    ToolsActive.append(getattr(ModuleActive[i], ImpA[i][1]))

ModulePassive = list()
ToolsPassive = list()
for i in np.arange(len(ImpB)):
    ModulePassive.append(__import__(ImpB[i][0], globals(), locals(), [ImpB[i][1]], -1))
    ToolsPassive.append(getattr(ModulePassive[i], ImpB[i][1]))
    #ModulePassive.append(importlib.import_module("tools."+ImpB[i][0]))
    #ToolsPassive.append(getattr(ModulePassive[i], ImpB[i][1]))

# This is in the file menu and not needed in the dictionaries below.
from chooseimport import ChooseImportTypes
from chooseimport import ChooseImportTypesModel
from comment import EditComment

ToolDict = dict()
ToolDict["A"] = ToolsActive
ToolDict["P"] = ToolsPassive


# Make the same for Menu Names in Tools
NameActive = list()
for i in np.arange(len(ImpA)):
    NameActive.append(ModuleActive[i].MENUINFO)
    
NamePassive = list()
for i in np.arange(len(ImpB)):
    NamePassive.append(ModulePassive[i].MENUINFO)


ToolName = dict()
ToolName["A"] = NameActive
ToolName["P"] = NamePassive

