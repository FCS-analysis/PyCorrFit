# -*- mode: python -*-
import codecs
import os
import platform
import sys

# path matplotlibrc
import matplotlib
mplrc = matplotlib.matplotlib_fname()
with open(mplrc) as fd:
    data = fd.readlines()
for ii, l in enumerate(data):
    if l.strip().startswith("backend "):
        data[ii] = "backend : WXAgg\n"
with open(mplrc, "w") as fd:
    fd.writelines(data)


if not os.path.exists("freeze_pyinstaller"):
    raise Exception("Please go to `PyCorrFit` directory.")

    
name = "PycorrFit"
DIR = os.path.realpath(".")
PyInstDir = os.path.join(DIR, "freeze_pyinstaller")
PCFDIR = os.path.join(DIR, "pycorrfit")
ProgPy = os.path.join(PCFDIR,"PyCorrFit.py")
ChLog = os.path.join(DIR,"ChangeLog.txt")
DocPDF = os.path.join(DIR,"doc/PyCorrFit_doc.pdf")
ICO = os.path.join(PyInstDir,"PyCorrFit.ico")

sys.path.append(DIR)

hiddenimports = ["scipy.io.matlab.streams",
                 "sympy.assumptions.handlers",
                 "sympy.assumptions.handlers.common",
                 "scipy.special._ufuncs_cxx",
                 "scipy.sparse.csgraph",
                 "scipy.sparse.csgraph._validation",
                 ]



## Create inno setup .iss file
import pycorrfit
version = pycorrfit.__version__
issfile = codecs.open(os.path.join(PyInstDir,"win7_innosetup.iss.dummy"), 'r', "utf-8")
iss = issfile.readlines()
issfile.close()
for i in range(len(iss)):
    if iss[i].strip().startswith("#define MyAppVersion"):
        iss[i] = '#define MyAppVersion "{:s}"\n'.format(version)
    if iss[i].strip().startswith("#define MyAppPlatform"):
        # sys.maxint returns the same for windows 64bit verions
        iss[i] = '#define MyAppPlatform "win_{}"\n'.format(platform.architecture()[0])
nissfile = codecs.open("win7_innosetup.iss", 'wb', "utf-8")
nissfile.write(u"\ufeff")
nissfile.writelines(iss)
nissfile.close()


a = Analysis([ProgPy],
             pathex=[DIR],
             hiddenimports=hiddenimports,
             hookspath=None)
a.datas += [('doc\\ChangeLog.txt', ChLog, 'DATA'),
            ('doc\\PyCorrFit_doc.pdf', DocPDF, 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name+'.exe',
          debug=False,
          strip=None,
          upx=True,
          icon=ICO,
          console=True )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=name)
