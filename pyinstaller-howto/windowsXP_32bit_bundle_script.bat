cd C:\Python27\PyCorrFit\pyinstaller
del /q /s ..\PyCorrFit\pyinstaller-howto\build
del /q /s ..\PyCorrFit\pyinstaller-howto\dist
python pyinstaller.py ..\PyCorrFit\pyinstaller-howto\PyCorrFit_win.spec