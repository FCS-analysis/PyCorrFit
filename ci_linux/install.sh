#!/bin/bash
set -e
deactivate
curl http://apt.wxwidgets.org/key.asc | sudo apt-key add - 
sudo apt-get update -qq
sudo apt-get install -qq python-pip python-wxgtk2.8
sudo pip install virtualenv
# use separate virtual environment
virtualenv --system-site-packages ~/env
source ~/env/bin/activate
pip install --upgrade pip
pip install scipy sympy numpy matplotlib cython

