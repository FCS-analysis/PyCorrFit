#!/bin/bash
set -e
sudo apt-get -y update
sudo apt-get -qq install python-pip python-wxgtk2.8 
# use separate virtual environment
pip install virtualenv
virtualenv --system-site-packages ~/env
pip install --upgrade pip
pip install scipy sympy numpy matplotlib cython
source ~/env/bin/activate
