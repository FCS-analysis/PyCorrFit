# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module doc
    *doc* is the documentation. Functions for various text output point here.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""
import sys
import csv
import matplotlib
import numpy
import os
import platform
import scipy

# This is a fake class for modules not available.
class Fake(object):
    def __init__(self):
        self.__version__ = "N/A"
        self.version = "N/A"

try:
    import sympy
except ImportError:
    print " Warning: module sympy not found!"
    sympy = Fake()
import tempfile
try:
    import urllib2
except ImportError:
    print " Warning: module urllib not found!"
    urllib = Fake()
try:
    import webbrowser
except ImportError:
    print " Warning: module webbrowser not found!"
    webbrowser = Fake()
import wx
import yaml

import readfiles


def description():
    return """PyCorrFit is a data displaying, fitting and processing
tool, targeted at fluorescence correlation
spectroscopy. PyCorrFit is written in Python."""

def info(version):
    """ Returns a little info about our program and what it can do.
    """
    textwin = u"""
    Paul Müller, Biotec - TU Dresden

    A flexible tool for fitting and analyzing correlation curves.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 1000 /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm^3 """

    textlin = """
    Paul Müller, Biotec - TU Dresden

    A flexible tool for fitting and analyzing correlation curves.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 1000 /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³ """
    if platform.system() != 'Linux':
        texta = textwin
    else:
        texta = textlin
        
    one = "    PyCorrFit version "+version
    two = "\n\n    Supported file types:"

    for item in readfiles.Filetypes.keys():
        if item.split("|")[0] != readfiles.Allsupfilesstring:
            two = two + "\n     - "+item.split("|")[0]
    
    return one + texta + two

    
def licence():
    return """PyCorrFit is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 2 of the License, 
or (at your option) any later version.

PyCorrFit is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License 
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


def saveCSVinfo(parent):
    a = "# This file was created using PyCorrFit version "+parent.version+".\n#\n"
    b = """# Lines starting with a '#' are treated as comments.
# The data is stored as CSV below this comment section.
# Data usually consists of lag times (channels) and
# the corresponding correlation function - experimental
# and fitted values plus resulting residuals.
# If this file is opened by PyCorrFit, only the first two
# columns will be imported as experimental data.
#
"""
    return a+b


def SessionReadme(parent):
    a = "This file was created using PyCorrFit version "+parent.version+"\n"
    b = """The .zip archive you are looking at is a stored session of PyCorrFit.
If you are interested in how the data is stored, you will find
out here. Most important are the dimensionalities:
Dimensionless representation:
 unit of time        : 1 ms
 unit of inverse time: 10³ /s
 unit of distance    : 100 nm
 unit of Diff.coeff  : 10 µm²/s
 unit of inverse area: 100 /µm²
 unit of inv. volume : 1000 /µm³
From there, the dimension of any parameter may be
calculated.

There are a number of files within this archive, 
depending on what was done during the session.

backgrounds.csv
 - Contains the list of backgrounds used
 - Averaged intensities in [kHz]

bg_trace*.csv (where * is an integer)
 - The trace of the background corresponding
   to the line number in backgrounds.csv
 - Time in [ms], Trace in [kHz]

comments.txt
 - Contains page titles and session comment
 - First n lines are titles, rest is session
   comment (where n is total number of pages)

data*.csv (where * is {Number of page})
 - Contains lag times [ms]
 - Contains experimental data, if available

Parameters.yaml
 - Contains all Parameters for each page
   Block format:

    - - '#{Number of page}: '       
      - {Internal model ID}
      - {List of parameters}
      - {List of checked parameters (for fitting)}
      - [{Min channel selected}, {Max channel selected}]
      - [{Weighted fit enabled}, {No. of bins from left and right}, {No. of knots (e.g. spline fitting)}]
      - [{Background to use (line in backgrounds.csv)}]
      - Data type is Cross-correlation?

 - Order in Parameters.yaml defines order of pages in a session
 - Order in Parameters.yaml defines order in comments.txt

Readme.txt (this file)

trace*.csv (where * is {Number of page} | appendix "A" or "B" point to
            the respective channels (only in cross-correlation mode))
 - Contains times [ms]
 - Contains countrates [kHz]
"""
    return a+b

def SoftwareUsed():
    """ Return some Information about the software used for this program """
    text = "Python "+sys.version+\
           "\n\nModules:"+\
           "\n - csv "+csv.__version__+\
           "\n - matplotlib "+matplotlib.__version__+\
           "\n - NumPy "+numpy.__version__+\
           "\n - os "+\
           "\n - platform "+platform.__version__+\
           "\n - SciPy "+scipy.__version__+\
           "\n - sympy "+sympy.__version__ +\
           "\n - sys "+\
           "\n - tempfile" +\
           "\n - urllib2 "+ urllib2.__version__ +\
           "\n - webbrowser"+\
           "\n - wxPython "+wx.__version__+\
           "\n - yaml "+yaml.__version__
    if hasattr(sys, 'frozen'):
        pyinst = "\n\nThis executable has been created using PyInstaller 1.5.1"
        text = text+pyinst
    return text
# Text that is displayed once someone wishes to average all his curves
average = """Create an average over all curves that were
imported using the same model as the
current page. A new page will be created
that contains the averaged data."""

averagedifflen = """It looks like you are trying to average over curves
that have different lengths. This was not
anticipated when writing this program."""

backgroundinit = """Correct the amplitude for non-correlated background.
The background intensity <B> can be either imported
from a blank measurement or set manually."""

#backgroundinit = """Set background correction with the background signal <B>
#to correct the amplitude of the correlation function by
#a factor of [<S>/(<S>-<B>)]² where <S> is the average
#trace signal of the measurement"""

# Channel selection tools text for  fixing channels
channelsel = """Channel settings will affect all subsequent panels
as long as this window stays open."""

# For the selection of types to import when doing import Data
chooseimport = """Several types of data were found in
the chosen file. Please select
what type(s) you would like to
import. """

# Standard homepage
HomePage = "http://fcstools.dyndns.org/pycorrfit/"
# Changelog filename
ChangeLog = "ChangeLog.txt"
# Github homepage
GitChangeLog = "https://raw.github.com/paulmueller/PyCorrFit/master/ChangeLog.txt"
GitHome = "https://github.com/paulmueller/PyCorrFit"








