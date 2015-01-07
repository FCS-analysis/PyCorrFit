cd %~dp0
cd ..
DEL /F /Q .\doc\PyScanFCS_doc.pdf

pyinstaller -y .\freeze_pyinstaller\PyCorrFit_win7.spec
