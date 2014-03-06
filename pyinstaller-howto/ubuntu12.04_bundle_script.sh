#!/bin/bash
# Works with 
# pyinstaller-develop fdeef345233bc13836f2b4bf6fa15ac55b8563ac
# **************** Change Variables Here ************
# Directory structure:
# ./PyCorrFit                     # git repository
# ./PyCorrFit/pyinstaller-2.0/    # Pyinstaller files
#PyInstaller="pyinstaller-2.0/"
PyInstaller="pyinstaller-pyinstaller-fdeef34/"
# Progname.py should be in the Progdir
Progname="PyCorrFit"
# We require a ChangeLog.txt and a source directory in the Progdir
# BASEDIR/PyCorrFit/pyinstaller-howto
BASEDIR=$(dirname $BASH_SOURCE)
cd $BASEDIR
BASEDIR=$(pwd)
cd "../../"
StartDir=$(pwd)"/"
Progdir=${StartDir}${Progname}"/"
# Virtualenv
PyInstallerDir=${StartDir}${Progname}"/"${PyInstaller}
Specfile=${BASEDIR}"/"${Progname}"_linux.spec"
echo $Specfile

echo "***************************************"
echo "* Creating "${Progname}" binary       *"
echo "***************************************"


# These lines were used to create a source zip file
# But we have a setup.py file now and don't need it anymore.
# We require a Progname_doc.tex in the source-doc directory
#DocDir=${StartDir}${Progname}"/doc-src/"
#BinDir=${StartDir}${Progname}"/"
#WD="/tmp/"${Progname}"/"
#mkdir -p $WD
#
#cp -R ${StartDir}${Progname}/src/* $WD
#cp -R ${StartDir}${Progname}/ChangeLog.txt $WD
#
#echo " *** Removing *.pyc files! *** "
#find  $WD -iname "*.pyc" -exec rm -r -f {} \;
#
#echo " *** Removing *.py~ files! *** "
#find  $WD -iname "*.py~" -exec rm -r -f {} \;
#
#echo " *** Adding documentation *** "
#cd $DocDir
#pdflatex -synctex=1 -interaction=nonstopmode ${Progname}_doc.tex >> /dev/null
#bibtex ${Progname}_doc.aux >> /dev/null
#bibtex ${Progname}_doc.aux >> /dev/null
#pdflatex -synctex=1 -interaction=nonstopmode ${Progname}_doc.tex >> /dev/null
#pdflatex -synctex=1 -interaction=nonstopmode ${Progname}_doc.tex >> /dev/null
#
#mkdir -p ${WD}/doc
#cp ${Progname}_doc.pdf ${WD}/doc/
#
#echo " *** Creating src zip file! *** "
#
#cd ${Progdir}
#zipname=${Progname}"_"
#zipname+=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
#zipname+="_src.zip"
#
#cd $WD"../"
#
#zip -r ${BinDir}${zipname} ${Progname} >> /dev/null

#rm -R $WD

cd $Progdir

if [ -f $Specfile ]
then
    # added following line (remove build directory beforehand!)
    # a.datas += [('doc/ChangeLog.txt', '/PATH/TO/PyCorrFit/ChangeLog.txt', 'DATA')]
    python ${PyInstallerDir}pyinstaller.py -F $Specfile
else
    python ${PyInstallerDir}pyinstaller.py -F ${Progdir}"src/"${Progname}".py"
fi
# Move the resulting file and rename it

cd ${Progdir}
name=${Progname}"_"
name+=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
name+="_Ubuntu12-04_"
name+=$(uname -r)
name+=".bin"

mv ${BASEDIR}"/dist/"${Progname} ${BASEDIR}${name}
# Cleanup
rm -R ${BASEDIR}"/build"
rm -R ${BASEDIR}"/dist"

# Zip the release
zip ${BASEDIR}${name}".zip" ${BASEDIR}${name}


