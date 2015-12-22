# -*- coding: utf-8 -*-
"""
PyCorrFit - module "tools"

This file contains tools, such as dialog boxes and other stuff,
that we need in PyCorrFit.

The tools work with triggers on page updates. Every tool has a 
function `OnPageChanged(self, page, trigger=None)` which is called
when something in the frontend chages. In order to minimize user
stall time, these functions are not executed for a certain list
of triggers that is defined in that function. This e.g. dramatically
speeds up tools like "Statistics view" when batch fitting.
    
Recognized triggers:
 tab_init           : initial stuff that is done for a new page
 tab_browse         : the tab has change and a new page is visible
 fit_batch          : the page is batch-fitted right now
 fit_finalize       : a (batch) fitting process is finished
 parm_batch         : parameters are changed in a batch process
 parm_finalize      : finished (batch) changing of page parameters
 page_add_batch     : when many pages are added at the same time
 page_add_finalize  : finished (batch) adding of pages
"""
# This file is necessary for this folder to become a module that can be 
# imported by PyCorrFit or other people.

import numpy as np                  # NumPy
import sys

from . import datarange
from . import background
from . import overlaycurves
from . import batchcontrol
from . import globalfit
from . import average
from . import simulation

from . import info
from . import statistics
from . import trace
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
from .chooseimport import ChooseImportTypes
from .chooseimport import ChooseImportTypesModel
from .comment import EditComment
# the "special" tool RangeSelector
from .parmrange import RangeSelector

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

