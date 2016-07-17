|PyCorrFit|
===========

|PyPI Version| |Build Status Win| |Build Status Mac| |Coverage Status|

A graphical fitting tool for fluorescence correlation spectroscopy (FCS) that comes with support for several file formats, can be applied to a large variety of problems, and attempts to be as user-friendly as possible. Some of the features are

- Averaging of curves
- Background correction
- Batch processing
- Overlay tool to identify outliers
- Fast simulation of model parameter behavior
- Session management
- User-defined model functions
- High quality plot export using LaTeX (bitmap or vector graphics)


Getting started
===============

Installation
------------
Installers for PyCorrFit are available at the `release page <https://github.com/FCS-analysis/PyCorrFit/releases>`__.

Documentation
-------------
A detailed documentation including an explanation of the graphical user interface and available model
functions is available as a `PDF file <https://github.com/FCS-analysis/PyCorrFit/wiki/PyCorrFit_doc.pdf>`__.

Wiki
----
If you are interested in a specific topic or wish to contribute with your own HowTo, have a look at the 
`PyCorrFit wiki <https://github.com/FCS-analysis/PyCorrFit/wiki/>`__. There you will also find information
on `how to write your own model functions <https://github.com/FCS-analysis/PyCorrFit/wiki/Writing-model-functions>`__.

Problems
--------
If you find a bug or need help with a specific topic, do not hesitate to ask a question
at the `issues page <https://github.com/FCS-analysis/PyCorrFit/wiki/Creating-a-new-issue>`__.


Advanced usage
--------------
If you have Python installed you can install PyCorrFit, including its scripting functionalities, from the Python package index:

::

    pip install pycorrfit[GUI]

More information is available in the `PyCorrFit wiki <https://github.com/FCS-analysis/PyCorrFit/wiki/Running-from-source>`__.


Information for developers
==========================

Running from source
-------------------
The easiest way to run PyCorrFit from source is to use
`Anaconda <http://continuum.io/downloads>`__. PyCorrFit requires wxPython which is not
available at the Python package index. Make sure you install a unicode version of wxPython.
Detailed installation instructions are `here <https://github.com/FCS-analysis/PyCorrFit/wiki/Running-from-source>`__.


Contributing
------------
The main branch for developing PyCorrFit is *develop*. Small changes that do not
break anything can be submitted to this branch.
If you want to do big changes, please (fork ShapeOut and) create a separate branch,
e.g. ``my_new_feature_dev``, and create a pull-request to *develop* once you are done making
your changes.
Please make sure to also update the 
`changelog <https://github.com/FCS-analysis/PyCorrFit/blob/develop/ChangeLog.txt>`__. 

Tests
-----
PyCorrFit is tested using pytest. If you have the time, please write test
methods for your code and put them in the ``tests`` directory. You may
run the tests manually by issuing:

::

    python setup.py test


Windows test binaries
---------------------
After each commit to the PyCorrFit repository, a binary installer is created
by `Appveyor <https://ci.appveyor.com/project/paulmueller/PyCorrFit>`__. Click
on a build and navigate to ``ARTIFACTS`` (upper right corner right under
the running time of the build). From there you can download the Windows installer of the commit.


.. |PyCorrFit| image:: https://raw.github.com/FCS-analysis/PyCorrFit/master/doc/Images/PyCorrFit_logo_dark.png
.. |PyPI Version| image:: http://img.shields.io/pypi/v/PyCorrFit.svg
   :target: https://pypi.python.org/pypi/pycorrfit
.. |Build Status Win| image:: https://img.shields.io/appveyor/ci/paulmueller/PyCorrFit/master.svg?label=build_win
   :target: https://ci.appveyor.com/project/paulmueller/pycorrfit
.. |Build Status Mac| image:: https://img.shields.io/travis/FCS-analysis/PyCorrFit/master.svg?label=build_mac
   :target: https://travis-ci.org/FCS-analysis/PyCorrFit
.. |Coverage Status| image:: https://img.shields.io/coveralls/FCS-analysis/PyCorrFit.svg
   :target: https://coveralls.io/r/FCS-analysis/PyCorrFit
