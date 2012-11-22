PyCorrFit
=========

data analysis software for fluorescence correlation spectroscopy (FCS)


LINUX
-------------------

On a standard Ubuntu-Linux 12.04 installation, install the following packages:

	python-numpy
	python-scipy
	python-sympy
	python-yaml
	python-wxtools
	python-wxgtk2.8-dbg
	python-matplotlib


For bleeding-edge packages, you want to run from a virtualenv. Perform the following tasks (wxPython currently not working):

	sudo apt-get install gfortran g++ liblapack-dev libblas-dev libpng12-dev libxft-dev make python-dev python-pip python-virtualenv

Create your own python environment

	virtualenv PyCorrFit_env

Activate the environment

	cd PyCorrFit_env
	source bin/activate

Install latest python packages into that environment:

	pip install -U matplotlib
	pip install -U numpy
	pip install -U scipy
	pip install -U sympy
	pip install pyyaml 

Not working:

	pip install wxPython



WINDOWS
-------------------

If you are having problems compiling with pyInstaller on windows, try to rename

C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.py to something else, like
C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.pyQQQ

This is aproblem caused by syntax differences of python3 and python2 which pyInstaller cannot yet tell
(exec_py3 is not python2 syntax).
http://code.google.com/p/mpmath/issues/detail?id=204 

Extended plotting features:
Windows:
- http://www.miktex.org/
  Install with automatic package download!
