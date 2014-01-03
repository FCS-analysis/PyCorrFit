# -*- coding: utf-8 -*-
""" PyCorrFit

    Module doc
    *doc* is the documentation. Functions for various text output point here.

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


import sys
import csv
import matplotlib
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


def GetLocationOfChangeLog(filename = "ChangeLog.txt"):
    locations = list()
    fname1 = os.path.realpath(__file__)
    # Try one directory up
    dir1 = os.path.dirname(fname1)+"/../"
    locations.append(os.path.realpath(dir1))
    # In case of distribution with .egg files (pip, easy_install)
    dir2 = os.path.dirname(fname1)+"/../pycorrfit_doc/"
    locations.append(os.path.realpath(dir2))
    ## freezed binaries:
    if hasattr(sys, 'frozen'):
        try:
            dir2 = sys._MEIPASS + "/doc/"
        except:
            dir2 = "./"
        locations.append(os.path.realpath(dir2))
    for loc in locations:
        thechl = os.path.join(loc,filename)
        if os.path.exists(thechl):
            return thechl
            break
    # if this does not work:
    return None


def GetLocationOfDocumentation(filename = "PyCorrFit_doc.pdf"):
    """ Returns the location of the documentation if there is any."""
    ## running from source
    locations = list()
    fname1 = os.path.realpath(__file__)
    # Documentation is usually one directory up
    dir1 = os.path.dirname(fname1)+"/../"
    locations.append(os.path.realpath(dir1))
    # In case of distribution with .egg files (pip, easy_install)
    dir2 = os.path.dirname(fname1)+"/../pycorrfit_doc/"
    locations.append(os.path.realpath(dir2))
    ## freezed binaries:
    if hasattr(sys, 'frozen'):
        try:
            dir2 = sys._MEIPASS + "/doc/"
        except:
            dir2 = "./"
        locations.append(os.path.realpath(dir2))
    for loc in locations:
        thedoc = os.path.join(loc,filename)
        if os.path.exists(thedoc):
            return thedoc
            break
    # if this does not work:
    return None


def info(version):
    """ Returns a little info about our program and what it can do.
    """
    textwin = u"""
    Copyright 2011-2012 Paul Müller, Biotec - TU Dresden

    A versatile tool for fitting and analyzing correlation curves.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 1000 /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm^3 """
    textlin = """
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
    one = "    PyCorrFit version "+version+"\n\n"
    two = "\n\n    Supported file types:"
    for item in readfiles.Filetypes.keys():
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
        pyinst = "\n\nThis executable has been created using PyInstaller."
        text = text+pyinst
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
