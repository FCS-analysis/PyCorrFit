Appveyor recipe
---------------

Files that are used by ../appveyor.yaml to build a Windows installer

- `install.ps1` : install Miniconda   
  powershell script that donwloads and installs stuff

- `pinned` : pin packages in Anaconda   
  For example, NumPy is pinned to something <1.9.0, because
  WxPython will not work with numpy>1.9.0 due to this bug:
  http://trac.wxwidgets.org/ticket/16590

- `PyCorrFit_win7.spec` : PyInstaller spec file      
  The configuration for building the binaries with PyInstaller

- `run_with_compiler.cmd` : powershell tools   
  Something required for running stuff on i386 and x64

- `win_innosetup.iss.dummy` : InnoSetup file   
  Configuration for building the installer

