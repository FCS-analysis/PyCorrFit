# -*- coding: utf-8 -*-
"""
PyCorrFit

Documentation and program specific information
"""


import sys

# This is a fake class for modules not available.
class Fake(object):
    def __init__(self):
        self.__version__ = "N/A"
        self.version = "N/A"
        self.use = lambda x: None        
try:
    import matplotlib
except:
    # Create fake opbject for matplotlib
    matplotlib = Fake()
    
# We do catch warnings about performing this before matplotlib.backends stuff
#matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets for dialogs
import numpy
import os
import platform
import scipy

try:
    import sympy
except ImportError:
    print " Warning: module sympy not found!"
    sympy = Fake()

import wx
import yaml

import readfiles


def GetLocationOfFile(filename):
    dirname = os.path.dirname(os.path.abspath(__file__))
    locations = [
                    os.path.realpath(dirname+"/../"),
                    os.path.realpath(dirname+"/../pycorrfit_doc/"),
                    os.path.realpath(dirname+"/../doc/"),
                ]

    for i in range(len(locations)):
        # check /usr/lib64/32 -> /usr/lib
        for larch in ["lib32", "lib64"]:
            if dirname.count(larch):
                locations.append(locations[i].replace(larch, "lib", 1))
    
    ## freezed binaries:
    if hasattr(sys, 'frozen'):
        try:
            adir = sys._MEIPASS + "/doc/"  # @UndefinedVariable
        except:
            adir = "./"
        locations.append(os.path.realpath(adir))
    for loc in locations:
        thechl = os.path.join(loc,filename)
        if os.path.exists(thechl):
            return thechl
            break
    # if this does not work:
    return None


def GetLocationOfChangeLog(filename = "ChangeLog.txt"):
    return GetLocationOfFile(filename)


def GetLocationOfDocumentation(filename = "PyCorrFit_doc.pdf"):
    """ Returns the location of the documentation if there is any."""
    return GetLocationOfFile(filename)


def info(version):
    """ Returns a little info about our program and what it can do.
    """
    textwin = u"""
    Copyright 2011-2012 Paul Mueller, Biotec - TU Dresden

    A versatile tool for fitting and analyzing correlation curves.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 1000 /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 um^2/s
    unit of inverse area: 100 /um^2
    unit of inv. volume : 1000 /um^3 """
    textlin = u"""
    © 2011-2012 Paul Müller, Biotec - TU Dresden

    A versatile tool for fitting and analyzing correlation curves.

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
    one = u"    PyCorrFit version "+version+"\n\n"
    two = u"\n\n    Supported file types:"
    keys = readfiles.Filetypes.keys()
    keys.sort()
    for item in keys:
        if item.split("|")[0] != readfiles.Allsupfilesstring:
            two = two + "\n     - "+item.split("|")[0]
    lizenz = ""
    for line in licence().splitlines():
        lizenz += "    "+line+"\n"
    return one + lizenz + texta + two

    
def licence():
    return """PyCorrFit is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published 
by the Free Software Foundation, either version 2 of the License, 
or (at your option) any later version.

PyCorrFit is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License 
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


def SoftwareUsed():
    """ Return some Information about the software used for this program """
    text = "Python "+sys.version+\
           "\n\nModules:"+\
           "\n - cython "+\
           "\n - matplotlib "+matplotlib.__version__+\
           "\n - NumPy "+numpy.__version__+\
           "\n - PyYAML "+yaml.__version__ +\
           "\n - SciPy "+scipy.__version__+\
           "\n - sympy "+sympy.__version__ +\
           "\n - wxPython "+wx.__version__
    # Other software
    text += "\n\nOther software:"+\
            "\n - FCS_point_correlator (9311a5c15e)" +\
            "\n    PicoQuant file format for Python by Dominic Waithe"
    if hasattr(sys, 'frozen'):
        pyinst = "\n\nThis executable has been created using PyInstaller."
        text += pyinst
        if 'Anaconda' in sys.version or "Continuum Analytics" in sys.version:
            conda = "\n\nPowered by Anaconda"
            text += conda
    return text


# Standard homepage
HomePage = "http://pycorrfit.craban.de/"
# Changelog filename
ChangeLog = "ChangeLog.txt"
StaticChangeLog = GetLocationOfChangeLog(ChangeLog)

# Check if we can extract the version
try:
    clfile = open(StaticChangeLog, 'r')
    __version__ = clfile.readline().strip()
    clfile.close()     
except:
    __version__ = "0.0.0-unknown"
    
    
# Github homepage
GitChLog = "https://raw.github.com/paulmueller/PyCorrFit/master/ChangeLog.txt"
GitHome = "https://github.com/paulmueller/PyCorrFit"
GitWiki = "https://github.com/paulmueller/PyCorrFit/wiki"
