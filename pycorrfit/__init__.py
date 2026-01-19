"""
PyCorrFit is a tool to fit fluorescence correlation spectroscopy
data on a logarithmic scale.
"""

from importlib.metadata import PackageNotFoundError, version

from . import meta, models, openfile, readfiles
from .correlation import Correlation
from .fit import Fit
from .trace import Trace

try:
    __version__ = version("pycorrfit")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"


__author__ = "Paul Müller"
__license__ = "GPL v2"
__all__ = ["meta", "models", "openfile", "readfiles", "Fit", "Trace", "Correlation"]
