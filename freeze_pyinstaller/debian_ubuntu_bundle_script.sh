#!/bin/bash
Progname="PyCorrFit"
Prgname_lower="pycorrfit"
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

echo $Specfile

cd $StartDir

if [ -f $Specfile ]
then
    # added following line (remove build directory beforehand!)
    # a.datas += [('doc/ChangeLog.txt', '/PATH/TO/PyCorrFit/ChangeLog.txt', 'DATA')]
    pyinstaller -F $Specfile
else
    echo "Could not find specfile. Proceeding without..."
    sleep 1
    pyinstaller -F ${Progdir}${Prgname_lower}"/"${Progname}".py"
fi

# zip the release
zip -j ${Zipname} "dist/"${Progname} ${Docname} ${Changelogname}
