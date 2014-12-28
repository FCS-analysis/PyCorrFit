# -*- mode: python -*-
a = Analysis(['pycorrfit/PyCorrFit.py'],
             hiddenimports=["sympy.assumptions.handlers", # sympy
                            "sympy.assumptions.handlers.common",
                            "scipy.special._ufuncs_cxx"],
             hookspath=None)
a.datas += [('doc/ChangeLog.txt', 'ChangeLog.txt', 'DATA'),
            ('doc/PyCorrFit_doc.pdf', 'doc/PyCorrFit_doc.pdf', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'PyCorrFit'),
          debug=False,
          strip=None,
          upx=True,
          console=False
         )
