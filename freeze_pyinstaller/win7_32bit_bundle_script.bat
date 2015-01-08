cd %~dp0
cd ..
DEL /F /Q .\doc\PyCorrFit_doc.pdf
python setup.py build_ext --inplace

pyinstaller -y .\freeze_pyinstaller\PyCorrFit_win7.spec
