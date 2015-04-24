#!/usr/bin/env python
# To just compile the cython part in-place:
#  python setup.py build_ext --inplace
# To create a distribution package for pip or easy-install:
#  python setup.py sdist
# To create wheels package and upload securely
#  pip install wheel twine
#  python setup.py bdist wheel
from __future__ import print_function
from setuptools import setup, find_packages, Extension
import sys

from os.path import join, dirname, realpath, exists
from warnings import warn

# The next three lines are necessary for setup.py install to include
# ChangeLog and Documentation of PyCorrFit
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


# Cython only where available
try:
    from Cython.Distutils import build_ext
    import numpy as np
except ImportError:
    print("Cython or NumPy not available:", sys.exc_info())
    EXTENSIONS = []
else:
    EXTENSIONS = [Extension("pycorrfit.readfiles.read_pt3_scripts.fib4",
                        ["pycorrfit/readfiles/read_pt3_scripts/fib4.pyx"],
                        libraries=[],
                        include_dirs=[np.get_include()]
                        )
              ]


# Download documentation if it was not compiled
Documentation = join(dirname(realpath(__file__)), "doc/PyCorrFit_doc.pdf")
webdoc = "https://github.com/paulmueller/PyCorrFit/wiki/PyCorrFit_doc.pdf"
if not exists(Documentation):
    print("Downloading {} from {}".format(Documentation, webdoc))
    import urllib
    #testfile = urllib.URLopener()
    urllib.urlretrieve(webdoc, Documentation)
    

# Get the version of PyCorrFit from the Changelog.txt
StaticChangeLog = join(dirname(realpath(__file__)), "ChangeLog.txt")
try:
    clfile = open(StaticChangeLog, 'r')
    version = clfile.readline().strip()
    clfile.close()     
except:
    warn("Could not find 'ChangeLog.txt'. PyCorrFit version is unknown.")
    version = "0.0.0-unknown"




name = 'pycorrfit'

setup(
    name=name,
    author='Paul Mueller',
    author_email='paul.mueller@biotec.tu-dresden.de',
    url='https://github.com/paulmueller/PyCorrFit',
    version=version,
    packages=['pycorrfit',
              'pycorrfit.models',
              'pycorrfit.readfiles',
              'pycorrfit.tools'],
    package_dir={'pycorrfit': 'pycorrfit',
                 'pycorrfit.models': 'pycorrfit/models',
                 'pycorrfit.readfiles': 'pycorrfit/readfiles',
                 'pycorrfit.tools': 'pycorrfit/tools'},
    data_files=[('pycorrfit_doc', ['ChangeLog.txt', 'doc/PyCorrFit_doc.pdf'])],
    license="GPL v2",
    description='Scientific tool for fitting correlation curves on a logarithmic plot.',
    long_description=open(join(dirname(__file__), 'Readme.txt')).read(),
    include_package_data=True,
    cmdclass={"build_ext": build_ext},
    ext_modules=EXTENSIONS,
    setup_requires=[
        "cython",
        ],
    install_requires=[
        "NumPy >= 1.5.1",
        "SciPy >= 0.8.0",
        "PyYAML >= 3.09",
        ],
    extras_require = {
        # If you need the GUI of this project in your project, add
        # "thisproject[GUI]" to your install_requires
        # Graphical User Interface
        'GUI':  ["wxPython", "matplotlib >= 1.1.0"],
        # User Model Checks
        'UMC': ["sympy >= 0.7.2"],
        },
    keywords=["fcs", "fluorescence", "correlation", "spectroscopy",
              "tir", "fitting"
        ],
    classifiers= [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
        ],
    platforms=['ALL'],
    entry_points={
       "gui_scripts": ["{name:s}={name:s}:Main [GUI]".format(
                                                       **{"name":name})]
       }
    )


