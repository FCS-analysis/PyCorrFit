#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import join, dirname, realpath
from warnings import warn

# The next three lines are necessary for setup.py install to include
# ChangeLog and Documentation of PyCorrFit
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


# Get the version of PyCorrFit from the Changelog.txt
StaticChangeLog = join(dirname(realpath(__file__)), "ChangeLog.txt")
try:
    clfile = open(StaticChangeLog, 'r')
    version = clfile.readline().strip()
    clfile.close()     
except:
    warn("Could not find 'ChangeLog.txt'. PyCorrFit version is unknown.")
    version = "0.0.0-unknown"

setup(
    name='pycorrfit',
    author='Paul Mueller',
    author_email='paul.mueller@biotec.tu-dresden.de',
    url='https://github.com/paulmueller/PyCorrFit',
    version=version,
    packages=['pycorrfit',
              'pycorrfit.models',
              'pycorrfit.readfiles',
              'pycorrfit.tools'],
    package_dir={'pycorrfit': 'src',
                 'pycorrfit.models': 'src/models',
                 'pycorrfit.readfiles': 'src/readfiles',
                 'pycorrfit.tools': 'src/tools'},
    data_files=[('pycorrfit_doc', ['ChangeLog.txt', 'PyCorrFit_doc.pdf'])],
    license="GPL v2",
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    scripts=['bin/pycorrfit'],
    include_package_data=True,
    install_requires=[
        "NumPy >= 1.5.1",
        "SciPy >= 0.8.0",
        "sympy >= 0.7.2",
        "PyYAML >= 3.09",
        "wxPython >= 2.8.10.1",
        "matplotlib >= 1.1.0"]
    )


