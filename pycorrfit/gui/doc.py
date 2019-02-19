"""Documentation and program specific information"""
import platform
import sys

import lmfit
import matplotlib
import numpy
import scipy
import simplejson
import sympy
import wx
import yaml

import pycorrfit
from pycorrfit import readfiles, meta
from pycorrfit.readfiles import read_pt3_scripts


__version__ = pycorrfit.__version__


def GetLocationOfChangeLog(filename="CHANGELOG"):
    """Find location of CHANGELOG"""
    return meta.get_file_location(filename)


def GetLocationOfDocumentation(filename="PyCorrFit_doc.pdf"):
    """Return the location of the documentation if there is any"""
    return meta.get_file_location(filename)


def info(version):
    """Return info about PyCorrFit and what it can do"""
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
    keys = readfiles.filetypes_dict.keys()
    keys = sorted(list(keys))
    for item in keys:
        if item.split("|")[0] != readfiles.ALL_SUP_STRING:
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
    """Return some Information about the software used for this program"""
    text = "Python "+sys.version +\
           "\n\nModules:" +\
           "\n - cython " +\
           "\n - lmfit "+lmfit.__version__ +\
           "\n - matplotlib "+matplotlib.__version__ +\
           "\n - NumPy "+numpy.__version__ +\
           "\n - PyYAML "+yaml.__version__ +\
           "\n - SciPy "+scipy.__version__ +\
           "\n - simplejson "+simplejson.__version__ +\
           "\n - sympy "+sympy.__version__ +\
           "\n - wxPython "+wx.__version__
    # Other software
    text += "\n\nOther software:" +\
            "\n - FCS_point_correlator ({})".format(read_pt3_scripts.version) +\
            "\n    PicoQuant file format for Python by Dominic Waithe"
    if hasattr(sys, 'frozen'):
        pyinst = "\n\nThis executable has been created using PyInstaller."
        text += pyinst
        if 'Anaconda' in sys.version or "Continuum Analytics" in sys.version:
            conda = "\n\nPowered by Anaconda"
            text += conda
    return text


support = """
PyCorrFit has no funding and a vanishingly small developer community.
My personal objective is to keep PyCorrFit operational on Linux and
Windows which is currently limited by the free time I have available.

An active community is very important for an open source project such
as PyCorrFit. You can help this community grow (and thus help improve
PyCorrFit) in numerous ways:

1. \tTell your colleagues and peers about PyCorrFit. One of them might
   \tbe able to contribute to the project.

2. \tIf you need a new feature in PyCorrFit, publicly announce a bounty
   \tfor its implementation.

3. \tIf your research heavily relies on FCS, please consider diverting
   \tsome of your resources to the development of PyCorrFit.

4. \tYou don't have to be a Python programmer to contribute. If you are
   \tfamiliar with reStrucuredText or LaTeX, you might be able to help
   \tout with the online documentation.

5. \tPlease cite: Müller et al. Bioinformatics 30(17): 2532–2533, 2014

If you are planning to contribute to PyCorrFit, please contact me via
the PyCorrFit issue page on GitHub such that we may coordinate a pull
request.


Thank you!

Paul Müller (May 2018)
"""


# Standard homepage
HomePage = "http://pycorrfit.craban.de/"
# Changelog filename
ChangeLog = "CHANGELOG"
StaticChangeLog = GetLocationOfChangeLog(ChangeLog)


# Github homepage
GitChLog = "https://raw.github.com/FCS-analysis/PyCorrFit/master/CHANGELOG"
GitHome = "https://github.com/FCS-analysis/PyCorrFit"
GitWiki = "https://github.com/FCS-analysis/PyCorrFit/wiki"
