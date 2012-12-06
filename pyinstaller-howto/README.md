PyCorrFit - creating binaries with PyInstaller
=========

Usage
-------------------

Download PyInstaller v.2.0 from http://www.pyinstaller.org/
To create a single binary file, go to the unpacked pyinstaller directory and execute

    python pyinstaller.py /Path/To/PyCorrFit.py

Alternatively, there are ~.spec files and scripts for Windows XP / Ubuntu12.04 in this directory for bundling binary files.

Known problems
-------------------

- On Windows, PyInstaller v.2.0 might complain about a "_core_" module. This has been fixed in a later dev version (pyinstaller-6ca4af8 is working).

- PyInstaller does not yet seem to work with scipy version 0.11.0. Instead, use scipy version 0.10.1 (http://sourceforge.net/projects/scipy/files/scipy/). 

- If you are getting errors involving "_py3.py" files, try try to rename these files, e.g.

        C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.py 
    
    to something else, like

        C:\Python26\Lib\site-packages\sympy\mpmath\libmp\exec_py3.pyELSE

    This is a problem caused by syntax differences of python3 and python2 which pyInstaller cannot yet tell (exec_py3 is not python2 syntax). http://code.google.com/p/mpmath/issues/detail?id=204 


Windows (XP)
-------------------

Install "pywin32" from http://sourceforge.net/projects/pywin32/files/pywin32/ 

