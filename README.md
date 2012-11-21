PyCorrFit
=========

data analysis software for fluorescence correlation spectroscopy (FCS)

If you have problems compiling with pyInstaller on windows, try to rename

C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.py to something else, like
C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.pyQQQ

This is because python3 and python2 have different syntaxes and pyInstaller cannot yet
tell that the exec_py3 is not python2 syntax.

http://code.google.com/p/mpmath/issues/detail?id=204 


Packages:
python-numpy
python-scipy
python-yaml
python-wxtools
python-wxgtk2.8-dbg
python-matplotlib


https://launchpad.net/ubuntu/+source/python-numpy/
https://launchpad.net/ubuntu/+source/python-scipy/

http://code.google.com/p/sympy/downloads/list
python-sympy


Extended plotting features:
Windows:
- http://www.miktex.org/
  Install with automatic package download!
