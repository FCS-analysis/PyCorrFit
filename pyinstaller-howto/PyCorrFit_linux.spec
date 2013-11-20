# -*- mode: python -*-
a = Analysis(['PyCorrFit/src/PyCorrFit.py'],
             pathex=['pyinstaller-2.0'],
             hiddenimports=[],
             hookspath=None)
a.datas += [('doc/ChangeLog.txt', 'PyCorrFit/ChangeLog.txt', 'DATA'),
            ('doc/PyCorrFit_doc.pdf', 'PyCorrFit/PyCorrFit_doc.pdf', 'DATA')]
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
          console=True )
