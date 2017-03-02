#!/bin/bash
set -e
deactivate
sudo apt-get -qq update
sudo apt-get -qq install python-pip python-wxgtk2.8
sudo pip install virtualenv
# use separate virtual environment
virtualenv --system-site-packages ~/env
source ~/env/bin/activate
pip install --upgrade pip
pip install scipy sympy numpy matplotlib cython

