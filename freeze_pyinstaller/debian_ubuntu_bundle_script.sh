#!/bin/bash
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
Specfile=${BASEDIR}"/"${Progname}"_linux.spec"
codename=$(lsb_release -c | awk 'BEGIN { FS = "\t" }; { print $2 }')
distrib=$(lsb_release -i | awk 'BEGIN { FS = "\t" }; { print $2 }')
version=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
#Binname="dist/"${Progname}_${distrib}_${codename}_$(uname -r)".bin"
Zipname="dist/"${Progname}_${version}_${distrib}_${codename}_$(uname -r)".zip"
Env=".env_${Progname}"

echo $Specfile

cd $StartDir

echo "############"
echo "Checking pip"
echo "############"
# Check if pip is installed
if [ 1 -ne $(dpkg -s python-pip | grep -c "Status: install ok installed") ]; then
    echo "Please install package `python-pip`"
    exit
fi
if ! [ -e $Env ]; then
    virtualenv --system-site-packages $Env
    source $Env"/bin/activate"
    if [ $? -ne 0 ]; then
        echo "Error - Aborting"
        exit
    fi
    # Pyinstaller
    pip install git+git://github.com/pyinstaller/pyinstaller.git@779d07b236a943a4bf9d2b1a0ae3e0ebcc914798
fi
source $Env"/bin/activate"


echo "###################"
echo "Building Extensions"
echo "###################"
rm -f $Docname
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


echo "###################"
echo "Running Pyinstaller"
echo "###################"
pyinstaller -F $Specfile
if [ $? -ne 0 ]; then
    echo "Error - Aborting"
    exit
fi


echo "############"
echo "Creating Zip"
echo "############"
zip -j ${Zipname} "dist/"${Progname} ${Docname} ${Changelogname}
