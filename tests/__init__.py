# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 11:10:41 2018

@author: Germain
"""


from os import walk
import sys

for path, _, _ in walk('..'):
    sys.path.append(path)
