PyCorrFit documentation
=======================
This is the new sphinx-based documentation of PyCorrFit which will replace
the LaTeX-based documentation eventually.


To install the requirements for building the documentation, run

    pip install -r requirements.txt

To compile the documentation, run

    sphinx-build . _build


Notes
=====
To view the sphinx inventory of PyCorrFit, run

   python -m sphinx.ext.intersphinx 'http://pycorrfit.readthedocs.io/en/latest/objects.inv'
