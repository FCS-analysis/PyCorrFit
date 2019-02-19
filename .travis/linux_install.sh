#!/bin/bash
set -e
#deactivate
sudo apt-get update -qq
# Fixes the error:
# - ImportError: No module named _tkinter, please install the python-tk package
sudo apt-get install -qq python3-pip python3-tk virtualenv
# requirements for building wxPython4 on Ubuntu 17.10
# see https://github.com/wxWidgets/Phoenix/blob/master/README.rst
#sudo apt-get install -qq libgtk2.0 libgtk2.0-dev libwebkitgtk-dev dpkg-dev build-essential python3.6-dev libjpeg-dev libtiff-dev libsdl1.2-dev libnotify-dev freeglut3 freeglut3-dev libsm-dev libgtk-3-dev libwebkit2gtk-4.0-dev libxtst-dev libgstreamer-plugins-base1.0-dev
# use separate virtual environment
#virtualenv --system-site-packages -p python ~/env
#source ~/env/bin/activate
#pip install --upgrade pip
#pip install cython matplotlib lmfit numpy scipy sympy

