# -*- coding: utf-8 -*-
""" PyCorrFit

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

    Copyright (C) 2011-2012  Paul Müller

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License 
    along with this program. If not, see <http://www.gnu.org/licenses/>.
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

import datarange
import background
import overlaycurves
import batchcontrol
import globalfit
import average
import simulation

import info
import statistics
import trace
# Load all of the classes
# This also defines the order of the tools in the menu
ImpA = [ 
        ["datarange", "SelectChannels"],
        ["overlaycurves", "Wrapper_Tools"],
        ["batchcontrol", "BatchCtrl"],
        ["globalfit", "GlobalFit"],        
        ["average", "Average"],
        ["background", "BackgroundCorrection"]
       ]

ImpB = [
        ["trace", "ShowTrace"],
        ["statistics", "Stat"],
        ["info", "ShowInfo"],
        ["simulation", "Slide"]
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
# the "special" tool RangeSelector
from parmrange import RangeSelector

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

