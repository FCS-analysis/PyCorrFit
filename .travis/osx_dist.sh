#!/bin/bash
set -e

## Pyinstaller
python -m pip install pyinstaller

pyinstaller -y -F osx_pyinstaller.spec

mkdir dmgsrc
cp doc/*.pdf dmgsrc/ || exit 0
cp ChangeLog.txt dmgsrc/  || exit 0
cp -r "PyCorrFit.app" dmgsrc/  || exit 0
# hdiutil: create failed - error -5341
# http://stackoverflow.com/questions/18621467/error-creating-disk-image-using-hdutil
# https://discussions.apple.com/thread/4712306
touch dmgsrc/.Trash
rm -rf dmgsrc/.DStore
ls -la dmgsrc/
# hdiutil create PyCorrFit.dmg -srcfolder dmgsrc/ -ov
hdiutil create -volname "PyCorrFit_image" -megabytes 314m -format UDZO -imagekey zlib-level=9 -srcfolder dmgsrc -ov PyCorrFit.dmg
cp PyCorrFit.dmg dist/
