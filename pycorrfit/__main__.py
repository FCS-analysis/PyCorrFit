# -*- coding: utf-8 -*-
"""
Runs PyCorrFit
"""

from . import doc
from . import main

## VERSION
version = doc.__version__
__version__ = version

main.Main()
