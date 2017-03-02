#!/bin/bash
# remove any previously installed version of numpy
pip uninstall numpy
sudo apt-get -qy remove python-numpy
# install pcf dependencies
sudo apt-get -qy install  python-wxgtk2.8 python-numpy python-scipy python-pip cython python-matplotlib python-sympy

