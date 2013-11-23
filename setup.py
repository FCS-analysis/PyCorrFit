#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import join, dirname, realpath


# Get the version of PyCorrFit from the Changelog.txt
StaticChangeLog = join(dirname(realpath(__file__)), "ChangeLog.txt")
try:
    clfile = open(StaticChangeLog, 'r')
    version = clfile.readline().strip()
    clfile.close()     
except:
    version = "0.0.0-unknown"

setup(
    name='pycorrfit',
    author='Paul Mueller',
    author_email='paul.mueller@biotec.tu-dresden.de',
    url='https://github.com/paulmueller/PyCorrFit',
    version=version,
    packages=['pycorrfit','pycorrfit.models','pycorrfit.readfiles','pycorrfit.tools'],
    package_dir={'pycorrfit': 'src','pycorrfit.models': 'src/models','pycorrfit.readfiles': 'src/readfiles','pycorrfit.tools': 'src/tools'},
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    scripts=['bin/pycorrfit'],
    include_package_data=True,
    )
