#!/bin/bash
set -e
# a lot of cool formulae for scientific tools
#- brew tap homebrew/science
# numpy, scipy, matplotlib, ...
#- brew tap homebrew/python
#- brew tap homebrew/dupes
#- brew update
#- brew update && brew upgrade
#- brew install python --universal --framework
#- brew install wget
#- which python
#- python --version
#- export VERSIONER_PYTHON_PREFER_32_BIT=no
#- defaults write com.apple.versioner.python Prefer-32-Bit -bool no
#- brew unlink gcc
#- brew install gcc --universal
#- brew install freetype --universal
##- brew install numpy --universal
##- brew install scipy --universal
##- brew install matplotlib --universal
#
## https://github.com/Homebrew/homebrew/issues/34470
##- brew install wxpython --universal
##- brew install openblas
##- brew install gfortran

## wxPython
#- wget http://downloads.sourceforge.net/wxpython/wxPython3.0-osx-3.0.2.0-cocoa-py2.7.dmg
#sudo ./.travis/osx_install_dmg.sh

MINICONDA=Miniconda2-latest-MacOSX-x86_64.sh
wget http://repo.continuum.io/miniconda/${MINICONDA} -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b -p ${HOME}/miniconda
export PATH=${HOME}/miniconda/bin:$PATH
conda update --yes conda
travis_retry conda install --yes cython matplotlib numpy pip scipy wxpython
pip install -e .

# Patch wx.lib.plot
# http://trac.wxwidgets.org/ticket/16767#no1
#python -c "import wx; print wx.__version__"
#python -c "import wx; import wx.lib; import wx.lib.plot; print wx.lib.plot.__file__"
#- patch /usr/local/lib/wxPython-3.0.2.0/lib/python2.7/site-packages/wx-3.0-osx_cocoa/wx/lib/plot.py ./freeze_travis/wxPython-3.0.2.0-plot.patch
# wxPython is only available in 64bit version with homebrew
#- brew install wxpython

#- hdiutil create dist/hw.dmg -srcfolder dist/ -ov
#./freeze_travis/macOSx_bundle_script.sh

## Fixes
# matplotlib backend workaround
mkdir $HOME/.matplotlib
echo "backend: TkAgg" >> $HOME/.matplotlib/matplotlibrc

