#!/bin/bash
# pip install pyinstaller==2.1
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
SpecfileBIN=${BASEDIR}"/"${Progname}"_mac_bin.spec"
codename="MacOSx"
distrib=$(sw_vers -productVersion )
version=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
appn="./dist/${Progname}.app"
StarterScript="./freeze_pyinstaller/macOSx_script_starter.sh"
ZipnameBIN="dist/"${Progname}_${version}_${codename}_${distrib}"_bin.zip"
Zipname=${Progname}_${version}_${codename}_${distrib}"_app.zip"

echo $Specfile

cd $StartDir


echo "###################"
echo "Building Extensions"
echo "###################"
python setup.py build_ext --inplace
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
echo "Running Pyinstaller BIN"
echo "#######################"
pyinstaller --onefile -F $SpecfileBIN
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi


echo "################"
echo "Creating Zip BIN"
echo "################"
zip -j ${ZipnameBIN} "dist/"${Progname}"_bin" ${Docname} ${Changelogname}



echo "#######################"
echo "Running Pyinstaller APP"
echo "#######################"

if [ -e $appn ]; then rm -R $appn; fi

pyinstaller -y -F $Specfile
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi



# We need to run PyCorrFit in a separate Terminal to prevent this error
# from occuring:
#
# UnicodeDecodeError: 'ascii' codec can't decode byte 0xcf
# in position 0: ordinal not in range(128)
#
# tags: pyinstaller app bundling wxpython

# move aside the binary and replace with script
mv ${appn}"/Contents/MacOS/"${Progname} ${appn}"/Contents/MacOS/"${Progname}".bin"
cp ${StarterScript} ${appn}"/Contents/MacOS/"${Progname}

chmod +x ${appn}"/Contents/MacOS/"${Progname}


if [ -e $Zipname ]; then rm $Zipname; fi


echo "############"
echo "Creating Zip"
echo "############"
pushd dist
zip -r ${Zipname} ${Progname}".app"
popd
zip -j "./dist/"${Zipname} ${Docname} ${Changelogname}
