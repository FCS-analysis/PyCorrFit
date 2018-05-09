#!/usr/bin/env python
# -*- coding: utf-8 -*-
# To just compile the cython part in-place:
#  python setup.py build_ext --inplace
# To create a distribution package for pip or easy-install:
#  python setup.py sdist
# To create wheels package and upload securely
#  pip install wheel twine
#  python setup.py bdist wheel
from setuptools import setup, Extension
import sys
from Cython.Build import cythonize
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
    import numpy as np
except ImportError:
    print("NumPy not available. Building extensions "+
          "with this setup script will not work:", sys.exc_info())
    extensions = []
else:
    extensions = [Extension("pycorrfit.readfiles.read_pt3_scripts.fib4",
                            sources=["pycorrfit/readfiles/read_pt3_scripts/fib4.c"],
                            include_dirs=[np.get_include()]
                            )]


try:
    import urllib.request
except ImportError:
    pass
else:
    # Download documentation if it was not compiled with latex
    pdfdoc = join(dirname(realpath(__file__)), "doc/PyCorrFit_doc.pdf")
    webdoc = "https://github.com/FCS-analysis/PyCorrFit/wiki/PyCorrFit_doc.pdf"
    if not exists(pdfdoc):
        print("Downloading {} from {}".format(pdfdoc, webdoc))
        try:
            urllib.request.urlretrieve(webdoc, pdfdoc)
        except:
            print("Failed to download documentation.")

# Parameters
author = u"Paul Müller"
authors = [author]
description = 'Scientific tool for fitting correlation curves on a logarithmic plot.'
name = 'pycorrfit'
year = "2014"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
try:
    from _version import version
except:
    version = "unknown"

setup(

    author=author,
    author_email='paul.mueller@biotec.tu-dresden.de',
    classifiers= [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
        ],
    data_files=[('pycorrfit_doc', ['ChangeLog.txt', 'doc/PyCorrFit_doc.pdf'])],
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    include_package_data=True,
    keywords=["fcs", "fluorescence", "correlation", "spectroscopy",
              "tir", "fitting"
              ],
    license="GPL v2",
    name=name,
    platforms=['ALL'],
    url='https://github.com/FCS-analysis/PyCorrFit',
    version=version,
    # data files
    packages=['pycorrfit',
              'pycorrfit.models',
              'pycorrfit.readfiles',
              'pycorrfit.gui',
              'pycorrfit.gui.tools',
              ],
    package_dir={'pycorrfit': 'pycorrfit',
                 'pycorrfit.models': 'pycorrfit/models',
                 'pycorrfit.readfiles': 'pycorrfit/readfiles',
                 'pycorrfit.gui': 'pycorrfit/gui',
                 'pycorrfit.gui.tools': 'pycorrfit/gui/tools',
                 },
    # cython
    ext_modules = extensions,
    # requirements
    extras_require = {
        # If you need the GUI of this project in your project, add
        # "thisproject[GUI]" to your install_requires
        # Graphical User Interface
        'GUI':  ["wxPython",
                 "matplotlib >= 2.2.2",
                 "sympy >= 1.1.1",
                 "simplejson", # for updates
                 ],
        },
    install_requires=[
        "NumPy >= 1.14.2",
        "SciPy >= 1.0.1",
        "PyYAML >= 3.12",
        "lmfit >= 0.9.2",
        ],
    setup_requires=["Cython", 'pytest-runner', 'NumPy'],
    tests_require=["pytest", "urllib3", "simplejson"],
    # scripts
    entry_points={
       "gui_scripts": ["pycorrfit=pycorrfit.gui.main:Main"]
       }
    )
