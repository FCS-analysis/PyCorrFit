===============
About PyCorrFit
===============
In current biomedical research, fluorescence correlation spectroscopy (FCS) is
applied to characterize molecular dynamic processes in vitro and in living
cells. Commercial FCS setups only permit data analysis that is limited to a
specific instrument by the use of in-house file formats or a finite number of
implemented correlation model functions. PyCorrFit is a general-purpose FCS
evaluation software that, amongst other formats, supports the established
Zeiss ConfoCor3 ~.fcs file format. PyCorrFit comes with several built-in model
functions, covering a wide range of applications in standard confocal FCS. In
addition, it contains equations dealing with different excitation geometries
like total internal reflection (TIR).

Supported operating systems
---------------------------
- Windows 7 and higher
- Linux (Debian-based)
- Any other operating system with a Python 3.6 installation (via pip)

Supported filetypes
-------------------
- ALV correlators (~.ASC)
- Correlator.com (Flex) correlators (~.SIN)
- Zeiss ConfoCor3 (~.fcs)
- PicoQuant (~.pt3) as implemented by Dominic Waithe (https://github.com/dwaithe/FCS_point_correlator)
- PyCorrFit (~.csv)
- PyCorrFit session (~.pcfs)

Fitting
-------
- Pre-defined model functions
  (confocal FCS, TIR-FCS, triplet blinking, multiple components)
- Import of user-defined model functions
- Global fitting across multiple model functions or data sets
- Least squares fit using Levenberg-Marquard, Simplex, and more
- Weighted fitting with standard deviation

Tools and Features
------------------
- Averaging of curves
- Background correction
- Batch processing
- Overlay tool to identify outliers
- Fast simulation of model parameter behavior
- Session management
- High quality plot export using LaTeX
  (bitmap or vector graphics)

How to cite
-----------
Müller, P., Schwille, P., and Weidemann, T.
*PyCorrFit - generic data evaluation for fluorescence correlation spectroscopy.*
Bioinformatics 30(17):2532-2533 (2014).
DOI:`10.1093/bioinformatics/btu328 <http://dx.doi.org/10.1093/bioinformatics/btu328>`_

