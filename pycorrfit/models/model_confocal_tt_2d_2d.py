# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np

from .control import model_setup
from .cp_confocal import twod
from .cp_triplet import trip
from .cp_mix import double_pnum


# 2D + 2D + TT Gauß
# Model 6044
def CF_Gxyz_gauss_2D2DTT(parms, tau):
    u""" Two-component three-dimensional free diffusion
        with a Gaussian laser profile, including two triplet components.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle1 = F₁/(1+τ/τ₁)
        particle2 = α²*(1-F₁)/(1+τ/τ₂)
        triplet1 = 1 + T₁/(1-T₁)*exp(-τ/τ_trip₁)
        triplet2 = 1 + T₂/(1-T₂)*exp(-τ/τ_trip₂)
        norm = (F₁ + α*(1-F₁))²
        G = 1/n*(particle1 + particle2)*triplet1*triplet2/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0]  n        Effective number of particles in confocal volume
                      (n = n₁+n₂)
        [1]  τ₁       Diffusion time of particle species 1
        [2]  τ₂       Diffusion time of particle species 2
        [3]  F₁       Fraction of molecules of species 1 (n₁ = n*F₁)
                      0 <= F₁ <= 1
        [4]  α        Relative molecular brightness of particle
                      2 compared to particle 1 (α = q₂/q₁)
        [5]  τ_trip₁  Characteristic residence time in triplet state
        [6]  T₁       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [7]  τ_trip₂  Characteristic residence time in triplet state
        [8]  T₂       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [9]  offset
        *tau* - lag time
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    F=parms[3]
    alpha=parms[4]
    tautrip1=parms[5]
    T1=parms[6]
    tautrip2=parms[7]
    T2=parms[8]
    off=parms[9]

    g = double_pnum(n=n,
                    F1=F,
                    alpha=alpha,
                    comp1=twod,
                    comp2=twod,
                    kwargs1={"tau":tau,
                             "taudiff":taud1},
                    kwargs2={"tau":tau,
                             "taudiff":taud2},
                    )

    tr1 = trip(tau=tau, T=T1, tautrip=tautrip1)
    tr2 = trip(tau=tau, T=T2, tautrip=tautrip2)

    G = off + g * tr1 * tr2

    return G


def supplements(parms, countrate=None):
    u"""Supplementary parameters:
        [10]  n₁ = n*F₁     Particle number of species 1
        [11] n₂ = n*(1-F₁) Particle number of species 2
    """
    # We can only give you the effective particle number
    n = parms[0]
    F1 = parms[3]
    Info = list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n\u2081", n*F1])
    Info.append([u"n\u2082", n*(1.-F1)])
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


parms = [
            25,      # n
            5,       # taud1
            1000,    # taud2
            0.5,     # F
            1.0,     # alpha
            0.001,   # tautrip1
            0.01,    # T1
            0.002,   # tautrip2
            0.01,    # T2
            0.0      # offset
            ] 

## Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# F
boundaries[3] = [0,.9999999999999]
# T
boundaries[6] = [0,.9999999999999]
boundaries[8] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
             modelid=6044,
             name="Separate 2D diffusion with double triplet (confocal)",
             comp="T+T+2D+2D",
             mtype="Confocal (Gaussian) with double triplet",
             fctn=CF_Gxyz_gauss_2D2DTT,
             par_labels=[
                            u"n",
                            u"τ"+u"\u2081"+" [ms]",
                            u"τ"+u"\u2082"+" [ms]",
                            u"F"+u"\u2081",
                            u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                            u"τ_trip₁ [ms]",
                            u"T₁",
                            u"τ_trip₂ [ms]",
                            u"T₂",
                            u"offset"
                            ],
             par_values=parms,
             par_vary=[True, True, True, True, False, False, False, False, False, False],
             par_boundaries=boundaries,
             par_constraints=[[2, ">", 1], [5, "<", 1], [7, ">", 5]],
             par_hr_labels=[
                            u"n",
                            u"τ₁ [ms]",
                            u"τ₂ [ms]",
                            u"F₁",
                            u"\u03b1"+u" (q₂/q₁)", 
                            u"τ_trip₁ [µs]",
                            u"T₁",
                            u"τ_trip₂ [µs]",
                            u"T₂",
                            u"offset"
                            ],
             par_hr_factors=[
                            1.,     # n
                            1.,     # taud1
                            1.,     # taud2
                            1.,     # F
                            1.,     # alpha
                            1000.,  # tautrip1 [µs]
                            1.,     # T1
                            1000.,  # tautrip2 [µs]
                            1.,     # T2
                            1.      # offset
                            ],
             supplementary_method=supplements
            )
