# -*- mode: python -*-
from os.path import dirname, abspath, join

repo_dir = dirname(dirname(abspath(__file__)))

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

a = Analysis([join(repo_dir, 'pycorrfit/PyCorrFit.py')],
             hiddenimports=hiddenimports,
             hookspath=None)
a.datas += [('doc/ChangeLog.txt', join(repo_dir, 'ChangeLog.txt'), 'DATA'),
            ('doc/PyCorrFit_doc.pdf', join(repo_dir, 'doc/PyCorrFit_doc.pdf'), 'DATA')]
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
             name=join(repo_dir, 'dist/PyCorrFit.app'),
             icon=join(repo_dir, 'freeze_pyinstaller/PyCorrFit.icns')
             )
