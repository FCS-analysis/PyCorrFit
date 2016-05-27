#!/bin/bash
# pip install pyinstaller==2.1
export PATH=/usr/local/bin:$PATH
#export VERSIONER_PYTHON_PREFER_32_BIT=yes
#defaults write com.apple.versioner.python Prefer-32-Bit -bool yes

Progname="PyCorrFit"
# Go to base dir of repo
BASEDIR=$(dirname $0)
cd $BASEDIR
BASEDIR=$(pwd)
cd "../"
StartDir=$(pwd)"/"
Progdir=${StartDir}"/"
# We require a Progname_doc.tex in the source-doc directory
DocDir=${StartDir}"/doc/"
Docname=${DocDir}${Progname}"_doc.pdf"
Changelogname="ChangeLog.txt"
Specfile=${BASEDIR}"/"${Progname}"_mac.spec"
codename="MacOSx"
distrib=$(sw_vers -productVersion )
version=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
appn="./dist/${Progname}.app"
StarterScript="./freeze_pyinstaller/macOSx_script_starter.sh"
Zipname=${Progname}_${version}_${codename}_${distrib}"_app.zip"
DMGname=${Progname}_${version}_${codename}_${distrib}".dmg"

echo $Specfile

cd $StartDir


echo "###################"
echo "Building Extensions"
echo "###################"
rm -f $Docname
arch -i386  python setup.py build_ext --inplace
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi


echo "############################"
echo "Removing old build directory"
echo "############################"
rm -rf build
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi



echo "#######################"
echo "Running Pyinstaller APP"
echo "#######################"

if [ -e $appn ]; then rm -R $appn; fi

pyinstaller -y -F $Specfile
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi


if [ -e $Zipname ]; then rm $Zipname; fi


#echo "############"
#echo "Creating Zip"
#echo "############"
#pushd dist
#zip -r ${Zipname} ${Progname}".app"
#popd
#zip -j "./dist/"${Zipname} ${Docname} ${Changelogname}


echo "############"
echo "Creating DMG"
echo "############"
pushd dist
mkdir dmgsrc
cp ../doc/*.pdf dmgsrc/
cp ../ChangeLog.txt dmgsrc/
cp -r ${Progname}".app" dmgsrc/
# hdiutil: create failed - error -5341
# http://stackoverflow.com/questions/18621467/error-creating-disk-image-using-hdutil
# https://discussions.apple.com/thread/4712306
touch dmgsrc/.Trash
rm -rf dmgsrc/.DStore
ls -la dmgsrc/
# hdiutil create ${DMGname} -srcfolder dmgsrc/ -ov
hdiutil create -volname "PyCorrFit_image" -megabytes 314m -format UDZO -imagekey zlib-level=9 -srcfolder dmgsrc -ov ${DMGname}
popd
