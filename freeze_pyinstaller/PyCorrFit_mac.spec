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
             name='PyCorrFit.app',
             icon='pyinstaller-howto/PyCorrFit.icns')
