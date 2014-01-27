# -*- mode: python -*-
a = Analysis(['src/PyCorrFit.py'],
             #pathex=['pyinstaller-2.0'],
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
          name=os.path.join('dist', 'PyCorrFit'),
          debug=False,
          strip=None,
          upx=True,
          console=False )
#app = BUNDLE(exe,
#             name=os.path.join('dist', 'PyCorrFit.app'))
# APP bundling does not work because the app is somehow started with ASCII and not UTF-8 ???
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	Traceback (most recent call last):
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	  File "pyinstaller-howto/build/pyi.darwin/PyCorrFit_mac/out00-PYZ.pyz/frontend", line 214, in add_fitting_tab
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	  File "pyinstaller-howto/build/pyi.darwin/PyCorrFit_mac/out00-PYZ.pyz/page", line 156, in __init__
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	  File "pyinstaller-howto/build/pyi.darwin/PyCorrFit_mac/out00-PYZ.pyz/page", line 879, in settings
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	  File "pyinstaller-howto/build/pyi.darwin/PyCorrFit_mac/out00-PYZ.pyz/page", line 546, in MakeStaticBoxSizer
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	  File "pyinstaller-howto/build/pyi.darwin/PyCorrFit_mac/out00-PYZ.pyz/wx._controls", line 346, in __init__
#9/26/13 3:17:41 PM	[0x0-0x6a06a].PyCorrFit[2276]	UnicodeDecodeError: 'ascii' codec can't decode byte 0xcf in position 0: ordinal not in range(128)
