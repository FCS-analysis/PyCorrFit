# -*- mode: python -*-
a = Analysis(['src/PyCorrFit.py'],
             pathex=['PyInstaller-2.1'],
             hiddenimports=[],
             hookspath=None)
a.datas += [('doc/ChangeLog.txt', 'ChangeLog.txt', 'DATA'),
            ('doc/PyCorrFit_doc.pdf', 'PyCorrFit_doc.pdf', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'PyCorrFit_bin'),
          debug=False,
          strip=None,
          upx=True,
          console=False )

