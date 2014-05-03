#!/bin/bash

BASEDIR=$(dirname $BASH_SOURCE)
cd $BASEDIR
BASEDIR=$(pwd)
cd "../"

# successfully bundled PyCorrFit into binary but ".app" did not work.
# working with stable 2.0 release (MD5 19350c07632e4deef5f4ecf64a556637)
# and manual python 2.7 installation.

python ./Pyinstaller-2.1/pyinstaller.py -y ./pyinstaller-howto/PyCorrFit_mac.spec

# move aside the binary and replace with script

mv ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit.bin

cp ./pyinstaller-howto/macOSx_script_starter.sh ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit

chmod +x ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit
