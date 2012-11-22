PyCorrFit
=========

data analysis software for fluorescence correlation spectroscopy (FCS)


Ubuntu-Linux
-------------------

On a standard Ubuntu-Linux 12.04 installation, install the following packages:

	python-matplotlib
	python-numpy
	python-scipy
	python-sympy
	python-yaml
	python-wxtools
	python-wxgtk2.8-dbg

The following steps are optional but might solve some bugs that are present in packages from the Ubuntu-repositories.
Perform the following tasks in addition to the ones above:

	sudo apt-get install gfortran g++ liblapack-dev libblas-dev libpng12-dev libxft-dev make python-dev python-pip python-virtualenv

Create a virtual python environment with the system-site-packages option.

	virtualenv PyCorrFit_env --system-site-packages

Activate the virtual environment (Perform this step before executing "python PyCorrFit.py").

	cd PyCorrFit_env 
	source bin/activate

Install latest python packages into that environment:

	pip install -U numpy scipy matplotlib sympy




Windows (XP/7)
-------------------

If you are having problems compiling with pyInstaller on windows, try to rename

C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.py to something else, like
C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.pyQQQ

This is aproblem caused by syntax differences of python3 and python2 which pyInstaller cannot yet tell
(exec_py3 is not python2 syntax).
http://code.google.com/p/mpmath/issues/detail?id=204 

Extended plotting features:
Windows:
http://www.miktex.org/
  Install with automatic package download!
