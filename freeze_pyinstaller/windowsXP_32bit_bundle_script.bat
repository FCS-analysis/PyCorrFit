cd C:\Python27\pyinstaller
del /q /s ..\PyCorrFit\freeze_pyinstaller\build
del /q /s ..\PyCorrFit\freeze_pyinstaller\dist
python pyinstaller.py ..\PyCorrFit\freeze_pyinstaller\PyCorrFit_win.spec
