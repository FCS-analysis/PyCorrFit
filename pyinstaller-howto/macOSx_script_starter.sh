#!/bin/bash
#
# We need to run PyCorrFit in a separate Terminal to prevent this error
# from occuring:
#
# UnicodeDecodeError: 'ascii' codec can't decode byte 0xcf
# in position 0: ordinal not in range(128)
#
# tags: pyinstaller app bundling wxpython

cd $(dirname "$0")
open -a Terminal.app ./PyCorrFit.bin
