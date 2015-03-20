#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    In current biomedical research, fluorescence correlation spectroscopy (FCS)
    is applied to characterize molecular dynamic processes in vitro and in living
    cells. Commercial FCS setups only permit data analysis that is limited to a
    specific instrument by the use of in-house file formats or a finite number of
    implemented correlation model functions. PyCorrFit is a general-purpose FCS
    evaluation software that, amongst other formats, supports the established Zeiss
    ConfoCor3 ~.fcs file format. PyCorrFit comes with several built-in model
    functions, covering a wide range of applications in standard confocal FCS.
    In addition, it contains equations dealing with different excitation geometries
    like total internal reflection (TIR).

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

from . import doc
from . import models
from . import openfile
from . import readfiles

from .main import Main

__version__ = doc.__version__
__author__ = u"Paul Müller"
__license__ = "GPL v2"
