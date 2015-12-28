# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np

from .control import model_setup
from .cp_confocal import twod
from .cp_triplet import trip


# 2D simple gauss
def CF_Gxy_T_gauss(parms, tau):
    u""" Two-dimensional diffusion with a Gaussian laser profile,
        including a triplet component.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)

        G(τ) = offset + 1/( n * (1+τ/τ_diff) )*triplet
    
        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/(π*r₀²)

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal area
        [1] τ_diff  Characteristic residence time in confocal area
        [2] τ_trip  Characteristic residence time in triplet state
        [3] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [4] offset
        *tau* - lag time
    """
    n = parms[0]
    taudiff = parms[1]
    tautrip = parms[2]
    T = parms[3]
    dc = parms[4]

    triplet = trip(tau=tau, tautrip=tautrip, T=T)

    BB = twod(tau=tau, taudiff=taudiff)
    
    G = dc + 1/n * BB * triplet
    return G


def supplements(parms, countrate=None):
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


parms = [4.0, 0.4, 0.001, 0.01, 0.0]

## Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# F
boundaries[3] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]

model_setup(
             modelid=6002,
             name="2D diffusion with triplet (confocal)",
             comp="T+2D",
             mtype="Confocal (Gaussian) and triplet",
             fctn=CF_Gxy_T_gauss,
             par_labels=[  
                           u"n",
                           u"τ_diff [ms]",
                           u"τ_trip [ms]",
                           u"T",
                           u"offset"],
             par_values=parms,
             par_vary=[True, True, True, True, False],
             par_boundaries=boundaries,
             par_constraints=[[2, "<", 1]],
             par_hr_labels=[
                            u"n",
                            u"τ_diff [ms]",
                            u"τ_trip [µs]",
                            u"T",
                            u"offset"],
             par_hr_factors=[1., 1., 1000., 1., 1.],
             supplementary_method=supplements
            )
