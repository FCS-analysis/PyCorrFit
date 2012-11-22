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

import numpy as np                  # NumPy
import platform
import sys

import platform





## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
reload(sys)
sys.setdefaultencoding('utf-8')

# Load all of the classes
from average import Average
from background import BackgroundCorrection
from batch import BatchCtrl
from channels import SelectChannels
from globalfit import GlobalFit
from info import ShowInfo
from trace import ShowTrace
from statistics import Stat
from simulation import Slide


# from example import Tool

# This is in the file menu and not needed in the dictionaries below.
from batch import BatchImport
from chooseimport import ChooseImportTypes
from comment import EditComment



# Make a dictionary of Tools
ToolDict = dict()
# Make lists of tools for each dictionary entry
ToolsActive = [Average, BackgroundCorrection, BatchCtrl,  SelectChannels,
               GlobalFit, Slide]
ToolsPassive = [ShowInfo, ShowTrace, Stat]
ToolDict["A"] = ToolsActive
ToolDict["P"] = ToolsPassive


# Make the same for Menu Names in Tools
ToolName = dict()
NameActive = [
  ["&Average data", "Create an average curve from whole session."],
  ["&Background correction", "Open a file for background correction."],
  ["B&atch control", "Batch fitting."],
  ["&Data range selection", "Select an interval of lag times to be used for fitting."],
  ["&Global fitting", "Interconnect parameters from different measurements."],
  ["S&lider simulation", "Fast plotting for different parameters."]
             ]

NamePassive = [
    ["Page &info", "Display some information on the current page."],
    ["&Trace view", "Show the trace of an opened file."],
    ["&Statistics", "Show some session statistics."]
              ]


ToolName["A"] = NameActive
ToolName["P"] = NamePassive





