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


For developers
==============
If you would like to know how a contribution to PyCorrFit should look
like, please create an issue on GitHub and I will update this part
of the documentation.


Running from source
-------------------
The easiest way to run PyCorrFit from source is to use
`Anaconda <http://continuum.io/downloads>`_. PyCorrFit requires wxPython which is not
available at the Python package index. Make sure you install a unicode version of wxPython.
Detailed installation instructions are `here <https://github.com/FCS-analysis/PyCorrFit/wiki/Running-from-source>`_.


Contributing
------------
The main branch for developing PyCorrFit is *develop*. Small changes that do not
break anything can be submitted to this branch.
If you want to do big changes, please (fork ShapeOut and) create a separate branch,
e.g. ``my_new_feature_dev``, and create a pull-request to *develop* once you are done making
your changes.
Please make sure to also update the 
`changelog <https://github.com/FCS-analysis/PyCorrFit/blob/develop/CHANGELOG>`_. 

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
by `Appveyor <https://ci.appveyor.com/project/paulmueller/PyCorrFit>`_. Click
on a build and navigate to ``ARTIFACTS`` (upper right corner right under
the running time of the build). From there you can download the Windows installer of the commit.

