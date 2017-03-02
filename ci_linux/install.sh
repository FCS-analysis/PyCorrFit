#!/bin/bash
set -e
sudo apt-get -y update
sudo apt-get -y -qq install cython python-matplotlib python-numpy python-pip python-scipy python-sympy python-wxgtk2.8 
sudo pip install virtualenv
virtualenv --system-site-packages ~/env
source ~/env/bin/activate
