#!/bin/bash
set -e

MINICONDA=Miniconda3-4.4.10-MacOSX-x86_64.sh
wget http://repo.continuum.io/miniconda/${MINICONDA} -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b -p ${HOME}/miniconda
export PATH=${HOME}/miniconda/bin:$PATH
conda update --yes conda
travis_retry conda install --yes cython matplotlib numpy pip scipy wxpython
python -m pip install wheel
python -m pip install -e .

#- hdiutil create dist/hw.dmg -srcfolder dist/ -ov
#./freeze_travis/macOSx_bundle_script.sh

## Fixes
# matplotlib backend workaround
mkdir $HOME/.matplotlib
echo "backend: TkAgg" >> $HOME/.matplotlib/matplotlibrc

