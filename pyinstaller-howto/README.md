PyCorrFit - creating binaries with PyInstaller
=========

Usage
-------------------

Download PyInstaller v.2.0 from http://www.pyinstaller.org/
To create a single binary file, go to the unpacked pyinstaller directory and execute

    python pyinstaller.py /Path/To/PyCorrFit.py

Alternatively, there are ~.spec files and scripts for Windows XP / Ubuntu12.04 in this directory for bundling binary files.


Windows (XP)
-------------------

Install "pywin32" from http://sourceforge.net/projects/pywin32/files/pywin32/ 


Known problems
-------------------

- PyInstaller v.2.0 might complain about a "_core_" module. This has been fixed in a later dev version ([6ca4af80a2a621e0bd48a6d149aef7a023e10afc](https://github.com/pyinstaller/pyinstaller/tree/6ca4af80a2a621e0bd48a6d149aef7a023e10afc/) is working).

- PyInstaller does not yet seem to work with scipy version 0.11.0. Instead, use scipy version 0.10.1 (http://sourceforge.net/projects/scipy/files/scipy/). 

- If you are getting errors involving "_py3.py" files, try try to rename these files, e.g.

        C:\Python27\Lib\site-packages\sympy\mpmath\libmp\exec_py3.py 
    
    to something else, like

        C:\Python27\Lib\site-packages\sympy\mpmath\libmp\exec_py3.pyELSE

    This is a problem caused by syntax differences of python3 and python2 which pyInstaller cannot yet tell (exec_py3 is not python2 syntax). http://code.google.com/p/mpmath/issues/detail?id=204 

- If you are getting numpy errors after creating the .exe file ("No module named multiarray"). Try the following:
    1. Copy

            C:\Python27\Lib\site-packages\numpy-1.7.0-py2.7-win32.egg\numpy\core\include\numpy
    
        to 

            C:\Python27\include\
    2. Use the revision [6ca4af80a2a621e0bd48a6d149aef7a023e10afc](https://github.com/pyinstaller/pyinstaller/tree/6ca4af80a2a621e0bd48a6d149aef7a023e10afc/) of the pyinstaller-pyinstaller *develop* branch.   
    3. Make sure your windows user name does not conatin any unicode characters such as ü,é,etc. or create a new user.
