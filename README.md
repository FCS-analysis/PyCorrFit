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

Download and install Python 2.7.3

	http://www.python.org/download/releases/2.7.3/

Download and install setuptools (for Python 2.7)

	http://pypi.python.org/pypi/setuptools#windows

Add the following to your Windows PATH variable:

	C:\Python27;C:\Python27\Scripts

Then in a command line execute:

	easy_install numpy pyfits pyyaml 

matplotlib, scipy, sympy, and wxpython (unicode) have to be manually installed (for Python 2.7)

	http://sourceforge.net/projects/matplotlib/files/matplotlib/
	http://sourceforge.net/projects/scipy/files/scipy/
	http://code.google.com/p/sympy/downloads/list
	http://www.wxpython.org/download.php
	
In order to use the Latex-plotting features of PyCorrFit, install MikTex with (!) automatic apckage download.

	http://www.miktex.org/
