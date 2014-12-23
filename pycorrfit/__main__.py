# -*- coding: utf-8 -*-
"""
    When a membrane is scanned perpendicularly to its surface, the
    fluorescence signal originating from the membrane itself must be
    separated from the signal of the surrounding medium for an FCS
    analysis. PyCorrFit interactively extracts the fluctuating
    fluorescence signal from such measurements and applies a
    multiple-tau algorithm. The obtained correlation curves can be
    evaluated using PyCorrFit.

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
from . import main

## VERSION
version = doc.__version__
__version__ = version

main.Main()
