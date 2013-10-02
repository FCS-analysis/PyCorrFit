#!/bin/bash


# **************** Change Variables Here ************
# Directory structure:
# ./PyCorrFit           # git repository
# ./pyinstaller-2.0/    # Pyinstaller files
# ./Uploads             # Binary and zip files
PyInstaller="pyinstaller-2.0/"
#Uploads="Uploads/"
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
Virtualenv=${Progdir}"PyCorrFit_env/"
# We require a Progname_doc.tex in the source-doc directory
DocDir=${StartDir}${Progname}"/doc-src/"
#BinDir=${StartDir}${Uploads}
WD="/tmp/"${Progname}"/"
PyInstallerDir=${Progdir}${PyInstaller}
Specfile=${BASEDIR}"/"${Progname}"_linux.spec"
echo $Specfile


	# We are not creating zip files anymore, because they can be obtained from
	# GitHub releases. 
	#echo "***************************************"
	#echo "* Creating "${Progname}" binary and zip file *"
	#echo "***************************************"
	#
	#mkdir -p $WD
	#
	#cp -R ${StartDir}${Progname}/src/* $WD
	#cp -R ${StartDir}${Progname}/ChangeLog.txt $WD
	#
	#echo " *** Removing *.pyc files! *** "
	#find  $WD -iname "*.pyc" -exec rm -r -f {} \;
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
	#
	#rm -R $WD

echo " *** Creating binary file! *** "

source ${Virtualenv}"bin/activate"

cd $StartDir

if [ -f $Specfile ]
then
    # added following line (remove build directory beforehand!)
    # a.datas += [('doc/ChangeLog.txt', '/PATH/TO/PyCorrFit/ChangeLog.txt', 'DATA')]
    python ${PyInstallerDir}pyinstaller.py -F $Specfile
else
    python ${PyInstallerDir}pyinstaller.py -F ${Progdir}"src/"${Progname}".py"
fi
# Move the resulting file and rename it

chmod +x ${BASEDIR}"/dist/"${Progname} 

#cd ${Progdir}
#name=${Progname}"_"
#name+=$(head -n1 ./ChangeLog.txt | tr -d "\r\n")
#name+="_Ubuntu12.04_"
#name+=$(uname -r)
#name+="_amd64.bin"

#mv ${BASEDIR}"/dist/"${Progname} ${BinDir}${name}
#rm -R ${BASEDIR}"/build"
#rm -R ${BASEDIR}"/dist"



