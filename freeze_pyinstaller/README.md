PyCorrFit - creating binaries with PyInstaller
=========

Note that these files are only interesting to developers.

### Usage

I use PyInstaller (http://www.pyinstaller.org/) for packaging PyCorrFit. There are pre-defined spec-files for 
different platforms. From the PyCorrFit directory, just run

    pyinstaller freeze_pyinstaller/some_file.spec

or use the `.bat` or `.sh` files for your OS.

### Linux

- On Ubuntu 13.04 the following revision of Pyinstaller worked for me: [fdeef345233bc13836f2b4bf6fa15ac55b8563ac](https://github.com/pyinstaller/pyinstaller/tree/fdeef345233bc13836f2b4bf6fa15ac55b8563ac/)
- On Ubuntu 13.10 this one also worked: [1c35a62b65624623babc898ff0acd3080682cc20](https://github.com/matysek/pyinstaller/tree/1c35a62b65624623babc898ff0acd3080682cc20)
- On Debian Jessie use: [779d07b236a943a4bf9d2b1a0ae3e0ebcc914798](https://github.com/pyinstaller/pyinstaller/commit/779d07b236a943a4bf9d2b1a0ae3e0ebcc914798)


### Windows 7
This configuration works on a Windows 7 32bit machine:
- Install Anaconda 32 bit 2.1.0 system-wide
- (Delete the Anaconda3 folder if it exists)
- Install git (with git Bash)
- Install pywin32-219 (solves collect errors with empty file strings)
- install pyinstaller

        pip install git+git://github.com/pyinstaller/pyinstaller.git@779d07b236a943a4bf9d2b1a0ae3e0ebcc914798

- Clone this repository with git
- Run the executable `win7_32bit_bundle_script.bat`

If everything goes well, there will be a `dist` directory that contains the frozen PyCorrFit and, additionally, there will be a `win7_innosetup.iss` for building the installer with [Inno Setup](http://www.jrsoftware.org).

### Windows XP
Install Python and all packages required for PyCorrFit. Anaconda might work as well but is not tested.
Install "pywin32" from (http://sourceforge.net/projects/pywin32/files/pywin32/). Known Problems are:


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
