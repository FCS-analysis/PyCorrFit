#!/bin/bash
# Works with 
# pyinstaller-develop 1c35a62b65624623babc898ff0acd3080682cc20
# https://github.com/matysek/pyinstaller/tree/1c35a62b65624623babc898ff0acd3080682cc20
# **************** Change Variables Here ************
# Directory structure:
# ./PyCorrFit                     # git repository
PyInstaller="pyinstaller-1c35a62b65624623babc898ff0acd3080682cc20/"
# Progname.py should be in the Progdir
Progname="PyCorrFit"
# We require a ChangeLog.txt and a source directory in the Progdir
# BASEDIR/PyCorrFit/freeze_pyinstaller
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
    python ${PyInstallerDir}pyinstaller.py -F ${Progdir}"pycorrfit/"${Progname}".py"
fi
cd ${Progdir}
bname=${Progname}"_"
bname+=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
bname+="_Ubuntu13-10"

zname="Ubuntu13-10_"
zname+=${Progname}"_"
zname+=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
zname+=".zip"


#name+=$(uname -r)


mv ${Progdir}"dist/"${Progname} ${Progdir}"dist/"${bname}
# Cleanup
#rm -R ${Progdir}"/build"

# Zip the release
zip -j ${Progdir}"dist/"${zname} ${Progdir}"dist/"${bname}
