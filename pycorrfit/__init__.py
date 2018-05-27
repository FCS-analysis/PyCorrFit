"""
PyCorrFit is a tool to fit fluorescence correlation spectroscopy
data on a logarithmic scale.
"""
from . import meta
from . import models
from . import openfile
from . import readfiles

from .correlation import Correlation
from .fit import Fit
from .trace import Trace
from ._version import version as __version__

__author__ = u"Paul Müller"
__license__ = "GPL v2"
