# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np

from .control import model_setup
from .cp_confocal import threed
from .cp_triplet import trip


def CF_Gxyz_blink(parms, tau):
    u""" Three-dimanesional free diffusion with a Gaussian laser profile
        (eliptical), including a triplet component.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        G(τ) = offset + 1/( n*(1+τ/τ_diff) * sqrt(1 + τ/(SP²*τ_diff)) )
                    * ( 1+T/(1.-T)*exp(-τ/τ_trip) )

        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/( sqrt(π³)*r₀²*z₀ )

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
        [1] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [2] τ_trip  Characteristic residence time in triplet state
        [3] τ_diff  Characteristic residence time in confocal volume
        [4] SP      SP=z₀/r₀ Structural parameter,
                    describes the axis ratio of the confocal volume
        [5] offset
        *tau* - lag time
    """
    n = parms[0]
    T = parms[1]
    tautrip = parms[2]
    taudiff = parms[3]
    SP = parms[4]
    off = parms[5]

    AA = trip(tau, tautrip, T)
    BB = threed(tau, taudiff, SP)
    
    G = off + 1/n * AA * BB
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


parms = [4.0, 0.2, 0.001, 0.4, 5.0, 0.0]

## Boundaries
boundaries = [[0, np.inf]]*len(parms)
# T
boundaries[1] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
             modelid=6011,
             name="3D diffusion with triplet (confocal)",
             comp="T+3D",
             mtype="Confocal (Gaussian) and triplet",
             fctn=CF_Gxyz_blink,
             par_labels=[
                            u"n",
                            u"T",
                            u"τ_trip [ms]",
                            u"τ_diff [ms]",
                            u"SP",
                            u"offset"],
             par_values=parms,
             par_vary=[True, True, True, True, False, False],
             par_boundaries=boundaries,
             par_constraints=[[3, ">", 2]],
             par_hr_labels=[
                            u"n",
                            u"T",
                            u"τ_trip [µs]",
                            u"τ_diff [ms]",
                            u"SP",
                            u"offset"],
             par_hr_factors=[1., 1., 1000., 1., 1., 1.],
             supplementary_method=supplements
            )
