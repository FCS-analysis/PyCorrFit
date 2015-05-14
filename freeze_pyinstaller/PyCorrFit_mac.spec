#!/usr/bin/python
# -*- mode: python -*-
hiddenimports = [
 		 "scipy.io.matlab.streams",
		 "scipy.special",
		 "scipy.special.specfun",
		 "scipy.io.matlab.streams",
                 "sympy.assumptions.handlers",
                 "sympy.assumptions.handlers.common",
                 "scipy.special._ufuncs_cxx",
                 "scipy.sparse.csgraph",
                 "scipy.sparse.csgraph.shortest_path",
                 "scipy.sparse.csgraph._validation"]

a = Analysis(['pycorrfit/PyCorrFit.py'],
             hiddenimports=hiddenimports,
             hookspath=None)
a.datas += [('doc/ChangeLog.txt', 'ChangeLog.txt', 'DATA'),
            ('doc/PyCorrFit_doc.pdf', 'doc/PyCorrFit_doc.pdf', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='PyCorrFit',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='PyCorrFit')
app = BUNDLE(coll,
             name=os.path.join('dist', 'PyCorrFit.app'),
             icon='freeze_pyinstaller/PyCorrFit.icns')
