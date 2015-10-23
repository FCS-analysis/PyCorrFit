freeze_appveyor
---------------

files that are used by ../appveyor.yaml.

- `install.ps1` : install Miniconda   
  powershell script that donwloads and installs stuff

- `pinned` : pin packages in Anaconda   
  For example, NumPy is pinned to something <1.9.0, because
  WxPython will not work with numpy>1.9.0 due to this bug:
  http://trac.wxwidgets.org/ticket/16590

- `run_with_compiler.cmd` : powershell tools   
  Something required for running stuff on i386 and x64
