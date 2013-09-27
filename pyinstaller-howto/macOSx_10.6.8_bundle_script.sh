#!/bin/bash

BASEDIR=$(dirname $BASH_SOURCE)
cd $BASEDIR
BASEDIR=$(pwd)
cd "../"

# successfully bundled PyCorrFit into binary but ".app" did not work.
# working with stable 2.0 release (MD5 19350c07632e4deef5f4ecf64a556637)
# and manual python 2.7 installation.

python pyinstaller-2.0/pyinstaller.py -F pyinstaller-howto/PyCorrFit_mac.spec

#python pyinstaller-develop/pyinstaller.py -F pyinstaller-howto/PyCorrFit_mac.spec
