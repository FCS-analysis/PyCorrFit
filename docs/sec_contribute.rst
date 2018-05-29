==========
Contribute
==========


General remarks
===============
PyCorrFit has no funding and a vanishingly small developer community.
My personal objective is to keep PyCorrFit operational on Linux and
Windows which is currently limited by the free time I have available.

An active community is very important for an open source project such
as PyCorrFit. You can help this community grow (and thus help improve
PyCorrFit) in numerous ways:

1. Tell your colleagues and peers about PyCorrFit. One of them might
   be able to contribute to the project.

2. If you need a new feature in PyCorrFit, publicly announce a bounty
   for its implementation.

3. If your research heavily relies on FCS, please consider diverting
   some of your resources to the development of PyCorrFit.

4. You don't have to be a Python programmer to contribute. If you are
   familiar with reStrucuredText or LaTeX, you might be able to help
   out with the online documentation.

5. Please cite: Müller et al. Bioinformatics 30(17): 2532–2533, 2014

If you are planning to contribute to PyCorrFit, please contact me via
the PyCorrFit issue page on GitHub such that we may coordinate a pull
request.


For documentation writers
=========================
To build this documentation, fork PyCorrFit, navigate
to the `docs` (not `doc`) directory and run.

- ``pip install -r requirements.txt`` followed by
- ``sphinx-build . _build``.

This will create the html documentation on your computer. Syntax warnings and errors
will be displayed during the build (there should be none). After making your
changes to your forked branch, create a pull request on GitHub.

If you only found a typo or wish to make text-only changes, you can also
use the GitHub interface to edit the files (without testing the build
step on your computer).


For developers
==============

Running from source
-------------------
It is recommended to work with
`virtual environments <https://docs.python.org/3/tutorial/venv.html>`_.

Windows
~~~~~~~
The easiest way to run PyCorrFit from source on Windows is
`Anaconda <http://continuum.io/downloads>`_.

- ``conda install matplotlib numpy pip scipy wxpython``
- ``pip install cython wheel simplejson sympy lmfit``
- ``pip install -e .  # in the root directory of the repository`` 

Ubuntu 17.10
~~~~~~~~~~~~
PyCorrFit requires wxPython >= 4.0.1 which is not available as a binary
wheel on PyPI and thus must be built from the .tar.gz.
Install all dependencies (https://github.com/wxWidgets/Phoenix/blob/master/README.rst):

- ``pip install cython matplotlib lmfit numpy scipy sympy``
- ``sudo apt-get install -qq libgtk2.0 libgtk2.0-dev libwebkitgtk-dev dpkg-dev build-essential python3.6-dev libjpeg-dev libtiff-dev libsdl1.2-dev libnotify-dev freeglut3 freeglut3-dev libsm-dev libgtk-3-dev libwebkit2gtk-4.0-dev libxtst-dev libgstreamer-plugins-base1.0-dev``
- ``pip install wxPython  # this will take some time``
- ``pip install -e .  # in the root directory of the repository`` 

Testing
-------
PyCorrFit is tested using pytest. If you have the time, please write test
methods for your code and put them in the ``tests`` directory. You may
run all tests by issuing:

::

    python setup.py test


Pull request guidelines
-----------------------
Please fork PyCorrFit and create a pull request (PR) introducing your changes.

- A new PR should always be made into the `develop` branch.
- If a PR introduces a new functionality or fixes a bug, it should provide
  a test case, i.e. a new file or function in the `tests` directory
  (see `here <https://github.com/FCS-analysis/PyCorrFit/tree/develop/tests>`_
  for examples).
  Note that currently there is no recipe for testing the graphical user
  interface code.
- New code should follow the
  `style guide for Python <https://www.python.org/dev/peps/pep-0008/>`_.
  Please use `flake8 <http://flake8.pycqa.org/en/latest/index.html#quickstart>`_
  to check the files you changed or created.
- New code should be documented well.
- Make sure to update the `changelog <https://github.com/FCS-analysis/PyCorrFit/blob/develop/CHANGELOG>`_. 


Windows test binaries
---------------------
After each commit to the PyCorrFit repository, a binary installer is created
by `Appveyor <https://ci.appveyor.com/project/paulmueller/PyCorrFit>`_. Click
on a build and navigate to ``ARTIFACTS`` (upper right corner right under
the running time of the build). From there you can download the Windows
installer for the commit.

