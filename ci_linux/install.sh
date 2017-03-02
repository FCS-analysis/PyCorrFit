#!/bin/bash
set -e
deactivate
sudo apt-get update -qq
sudo apt-get install -qq python-pip
sudo pip install virtualenv
# use separate virtual environment
virtualenv --system-site-packages ~/env
source ~/env/bin/activate
pip install --upgrade pip
pip install cython matplotlib lmfit numpy scipy sympy

