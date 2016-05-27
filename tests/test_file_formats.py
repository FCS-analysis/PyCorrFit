#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test if pycorrfit can open all file formats.
"""
from __future__ import division, print_function

import sys
from os.path import abspath, dirname, split
import numpy as np

# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import data_file_dl
import pycorrfit

# Files that are known to not work
exclude = []


def test_open():
    """
    Try to open all files supported files
    """
    # get list of supported file extensions
    for ext in pycorrfit.readfiles.get_supported_extensions():
        files = data_file_dl.get_data_files_ext(ext)
        for f in files:
            if len([ex for ex in exclude if f.endswith(ex) ]):
                continue
            print(f)
            dn, fn = split(f)
            pycorrfit.readfiles.openAny(dn, fn)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
