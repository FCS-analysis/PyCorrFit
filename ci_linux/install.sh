#!/bin/bash
sudo apt-get -y update
sudo apt-get -y -qq install cython python-matplotlib python-numpy python-pip python-scipy python-sympy python-wxgtk2.8 virtualenv --system-site-packages ~/env
source ~/env/bin/activate
