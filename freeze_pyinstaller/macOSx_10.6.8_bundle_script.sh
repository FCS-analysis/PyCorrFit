#!/bin/bash
# pip install pyinstaller==2.1

BASEDIR=$(dirname $BASH_SOURCE)
cd $BASEDIR
BASEDIR=$(pwd)
cd "../"

# We need to run PyCorrFit in a separate Terminal to prevent this error
# from occuring:
#
# UnicodeDecodeError: 'ascii' codec can't decode byte 0xcf
# in position 0: ordinal not in range(128)
#
# tags: pyinstaller app bundling wxpython

appn="./PyCorrFit.app"

if [ -e $appn ]; then rm -R $appn; fi

pyinstaller -y ./freeze_pyinstaller/PyCorrFit_mac.spec

if [ $? != 0 ]; then exit 1; fi

# move aside the binary and replace with script
mv ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit.bin
cp ./freeze_pyinstaller/macOSx_script_starter.sh ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit

chmod +x ./dist/PyCorrFit.app/Contents/MacOS/PyCorrFit

vers=$(head -n1 ChangeLog.txt | tr -d '\r')

zipapp="./Mac_OSx_10.6+_PyCorrFit_${vers}_app.zip"

if [ -e $zipapp ]; then rm $zipapp; fi

pushd dist
zip -r -9 $zipapp $appn
popd

### binary file
binn="./PyCorrFit_bin"

if [ -e $binn ]; then rm $binn; fi

pyinstaller --onefile ./freeze_pyinstaller/PyCorrFit_mac_bin.spec

if [ $? != 0 ]; then exit 1; fi

pushd dist
zipbin="./Mac_OSx_10.6+_PyCorrFit_"${vers}"_bin.zip"
popd

if [ -e $zipbin ]; then rm $zipbin; fi

pushd dist
zip -1 $zipbin $binn
popd

