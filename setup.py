#!/usr/bin/env python
# -*- coding: utf-8 -*-
# To just compile the cython part in-place:
#  python setup.py build_ext --inplace
# To create a distribution package for pip or easy-install:
#  python setup.py sdist
# To create wheels package and upload securely
#  pip install wheel twine
#  python setup.py bdist wheel
from __future__ import print_function
from setuptools import setup, Extension, Command
import sys
import subprocess

from os.path import join, dirname, realpath, exists
from warnings import warn

# The next three lines are necessary for setup.py install to include
# ChangeLog and Documentation of PyCorrFit
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


# We don't need cython if a .whl package is available.
# Try to import cython and throw a warning if it does not work.
try:
    from Cython.Distutils import build_ext
    import numpy as np
except ImportError:
    print("Cython or NumPy not available. Building extensions "+
          "with this setup script will not work:", sys.exc_info())
    EXTENSIONS = []
    build_ext = None
else:
    EXTENSIONS = [Extension("pycorrfit.readfiles.read_pt3_scripts.fib4",
                        ["pycorrfit/readfiles/read_pt3_scripts/fib4.pyx"],
                        libraries=[],
                        include_dirs=[np.get_include()]
                        )
              ]


class PyTest(Command):
    """ Perform pytests
    """
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = subprocess.call([sys.executable, 'tests/runtests.py'])
        raise SystemExit(errno)

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

# Parameters
author = u"Paul Müller"
authors = [author]
description = 'Scientific tool for fitting correlation curves on a logarithmic plot.'
name = 'pycorrfit'
year = "2014"

setup(
    
    author=author,
    author_email='paul.mueller@biotec.tu-dresden.de',
    classifiers= [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
        ],
    data_files=[('pycorrfit_doc', ['ChangeLog.txt', 'doc/PyCorrFit_doc.pdf'])],
    description=description,
    include_package_data=True,
    keywords=["fcs", "fluorescence", "correlation", "spectroscopy",
              "tir", "fitting"
              ],
    license="GPL v2",
    long_description=open(join(dirname(__file__), 'Readme.txt')).read(),
    name=name,
    platforms=['ALL'],
    url='https://github.com/paulmueller/PyCorrFit',
    version=version,
    # data files
    packages=['pycorrfit',
              'pycorrfit.models',
              'pycorrfit.readfiles',
              'pycorrfit.tools'
              ],
    package_dir={'pycorrfit': 'pycorrfit',
                 'pycorrfit.models': 'pycorrfit/models',
                 'pycorrfit.readfiles': 'pycorrfit/readfiles',
                 'pycorrfit.tools': 'pycorrfit/tools'
                 },
    # cython
    ext_modules=EXTENSIONS,
    cmdclass={'build_ext': build_ext,
              'test': PyTest,
             },
    # requirements
    extras_require = {
        # If you need the GUI of this project in your project, add
        # "thisproject[GUI]" to your install_requires
        # Graphical User Interface
        'GUI':  ["wxPython", "matplotlib >= 1.1.0", "sympy >= 0.7.2"],
        },
    install_requires=[
        "NumPy >= 1.5.1",
        "SciPy >= 0.8.0",
        "PyYAML >= 3.09",
        ],
    setup_requires=["cython"],
    # scripts
    entry_points={
       "gui_scripts": ["{name:s}={name:s}:Main".format(
                                                       **{"name":name})]
       }
    )
