# -*- coding: utf-8 -*-
""" PyScanFCS loader
"""
from os.path import dirname, join, abspath, split

import sys
sys.path = [split(abspath(dirname(__file__)))[0]] + sys.path

import pycorrfit
pycorrfit.Main()
