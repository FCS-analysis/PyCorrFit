#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyCorrFit is a tool to fit correlation curves on a logarithmic scale.
"""

from . import doc
from . import models
from . import openfile
from . import readfiles
from . import fcs_data_set

from .main import Main

__version__ = doc.__version__
__author__ = u"Paul Müller"
__license__ = "GPL v2"
