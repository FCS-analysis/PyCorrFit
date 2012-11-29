PyCorrFit
=========

In current research, fluorescence correlation spectrsocopy (FCS) is  applied to
characterize dynamical processes in vitro and in vivo.  Commercial FCS setups only
permit data analysis that is limited to  a specific instrument by the use of in-house
file formats or a  finite number of implemented correlation model functions.
PyCorrFit is a general-purpose FCS evaluation software that,  amongst other formats,
supports the established ConfoCor3 ~.fcs  file format and which comes with several
built-in model functions,  covering a wide range of application including multiple
diffusional  species or total internal reflection (TIR-) FCS. For more information, visit the official homepage at http://fcstools.dyndns.org/pycorrfit.


This repository contains the source scripts of PyCorrFit. The Python language enables the program to be run on many different platforms. If you do not want to install Python on your system, checkout http://fcstools.dyndns.org/pycorrfit for potentially pre-compiled binaries.
If you want to compile the sources for your own system using [PyInstaller](http://www.pyinstaller.org), take a look at [README_PyInstaller.mdm](https://github.com/paulmueller/PyCorrFit/blob/master/README_PyInstaller.md).

To run PyCorrFit from source, download the contents of this repository, install the necessary modules (see below), and execute

	python PyCorrFit/source/PyCorrFit.py

Ubuntu-Linux
-------------------

- On a standard Ubuntu-Linux 12.04 installation, install these packages:

		python-matplotlib
		python-numpy
		python-scipy
		python-sympy
		python-yaml
		python-wxtools
		python-wxgtk2.8-dbg

- In order to use the Latex-plotting features of PyCorrFit, install

		texlive-latex-extra
		texlive-math-extra
		texlive-science

- The following steps are optional but might increase performance. Up-to-date python packages can easily be installed using pip. 
	- Install

			gfortran 
			g++ 
			liblapack-dev 
			libblas-dev 
			libpng12-dev 
			libxft-dev 
			make 
			python-dev 
			python-pip 
			python-virtualenv

	- Create a virtual python environment with the system-site-packages option.

			virtualenv PyCorrFit_env --system-site-packages

	- Activate the virtual environment (Perform this step before executing "python PyCorrFit.py").

			cd PyCorrFit_env 
			source bin/activate

	- Install latest python packages into that environment:

			pip install -U numpy scipy sympy


Windows (XP/7)
-------------------

- Download and install Python 2.7.3:   
	http://www.python.org/download/releases/2.7.3/

- Download and install setuptools (for Python 2.7):   
	http://pypi.python.org/pypi/setuptools#windows

- Add the following to your [Windows PATH variable](http://www.computerhope.com/issues/ch000549.htm):   

		C:\Python27;C:\Python27\Scripts

- In a [command line](http://www.computerhope.com/issues/chdos.htm), execute:   

		easy_install numpy pyfits pyyaml 

- matplotlib, scipy, sympy, and wxpython (unicode) have to be manually installed (for Python 2.7)   
	http://sourceforge.net/projects/matplotlib/files/matplotlib/ (unicode version)   
	http://sourceforge.net/projects/scipy/files/scipy/  	
	http://code.google.com/p/sympy/downloads/list   	
	http://www.wxpython.org/download.php   
	
- In order to use the Latex-plotting features of PyCorrFit, install MikTex with (!) automatic package download.   
	http://www.miktex.org/
