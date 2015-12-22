#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyCorrFit is a tool to fit correlation curves on a logarithmic scale.
"""

from . import meta
from . import models
from . import openfile
from . import readfiles

from .correlation import Correlation
from .fit import Fit
from .trace import Trace

__version__ = meta.get_version()
__author__ = u"Paul Müller"
__license__ = "GPL v2"

# Import the GUI in the end, because it needs `__version__`.
from .gui.main import Main