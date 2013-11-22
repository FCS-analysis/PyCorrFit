# -*- coding: utf-8 -*-
"""
PyCorrFit
Paul Müller, Biotec - TU Dresden

In current biomedical research, fluorescence correlation spectroscopy (FCS)
is applied to characterize molecular dynamic processes in vitro and in living
cells. Commercial FCS setups only permit data analysis that is limited to a
specific instrument by the use of in-house file formats or a finite number of
implemented correlation model functions. PyCorrFit is a general-purpose FCS
evaluation software that, amongst other formats, supports the established Zeiss
ConfoCor3 ~.fcs file format. PyCorrFit comes with several built-in model
functions, covering a wide range of applications in standard confocal FCS.
In addition, it contains equations dealing with different excitation geometries
like total internal reflection (TIR).
"""

import doc
import models
import readfiles

__version__ = doc.__version__
__author__ = "Paul Mueller"
__email__ = "paul.mueller@biotec.tu-dresden.de"

