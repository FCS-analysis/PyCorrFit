# -*- coding: utf-8 -*-
"""
This file contains a T+T+3D+3D model for confocal FCS.
"""
from __future__ import division

import numpy as np

# 3D + 3D + Triplet Gauß
# Model 6043
def CF_Gxyz_gauss_3D3DTT(parms, tau):
    u""" Two-component three-dimensional free diffusion
        with a Gaussian laser profile, including two triplet components.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle1 = F₁/( (1+τ/τ₁) * sqrt(1+τ/(τ₁*SP²)))
        particle2 = α*(1-F₁)/( (1+τ/τ₂) * sqrt(1+τ/(τ₂*SP²)))
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
        [4]  SP       SP=z₀/r₀, Structural parameter,
                      describes elongation of the confocal volume
        [5]  α        Relative molecular brightness of particle
                      2 compared to particle 1 (α = q₂/q₁)
        [6]  τ_trip₁  Characteristic residence time in triplet state
        [7]  T₁       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [8]  τ_trip₂  Characteristic residence time in triplet state
        [9]  T₂       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [10] offset
        *tau* - lag time
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip1=parms[6]
    T1=parms[7]
    tautrip2=parms[8]
    T2=parms[9]
    off=parms[10]

    particle1 = F/( (1+tau/taud1) * np.sqrt(1+tau/(taud1*SP**2)))
    particle2 = alpha**2*(1-F)/( (1+tau/taud2) * np.sqrt(1+tau/(taud2*SP**2)))
    # If the fraction of dark molecules is zero.
    if tautrip1 == 0 or T1 == 0:
        triplet1 = 1
    else:
        triplet1 = 1 + T1/(1-T1) * np.exp(-tau/tautrip1)
    if tautrip2 == 0 or T2 == 0:
        triplet2 = 1
    else:
        triplet2 = 1 + T2/(1-T2) * np.exp(-tau/tautrip2)
    # For alpha == 1, *norm* becomes one
    norm = (F + alpha*(1-F))**2

    G = 1/n*(particle1 + particle2)*triplet1*triplet2/norm + off
    return G

def get_boundaries_3D3DTT(parms):
    # strictly positive
    boundaries = [[0, np.inf]]*len(parms)
    # F
    boundaries[3] = [0,.9999999999999]
    # T
    boundaries[7] = [0,.9999999999999]
    boundaries[9] = [0,.9999999999999]
    boundaries[-1] = [-np.inf, np.inf]
    return boundaries


m_gauss_3d_3d_t_t_mix_6043 = [6043, "T+T+3D+3D",
                            u"Separate 3D diffusion + two triplet, Gauß",
                            CF_Gxyz_gauss_3D3DTT]

labels_6043  = [u"n",
                u"τ"+u"\u2081"+" [ms]",
                u"τ"+u"\u2082"+" [ms]",
                u"F"+u"\u2081", 
                u"SP",
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                u"τ_trip₁ [ms]",
                u"T₁",
                u"τ_trip₂ [ms]",
                u"T₂",
                u"offset"
                ]

labels_human_readable_6043  = [
                        u"n",
                        u"τ₁ [ms]",
                        u"τ₂ [ms]",
                        u"F₁", 
                        u"SP",
                        u"\u03b1"+u" (q₂/q₁)", 
                        u"τ_trip₁ [µs]",
                        u"T₁",
                        u"τ_trip₂ [µs]",
                        u"T₂",
                        u"offset"
                            ]

values_6043 = [ 
                25,      # n
                5,       # taud1
                1000,    # taud2
                0.5,     # F
                5,       # SP
                1.0,     # alpha
                0.002,   # tautrip1
                0.01,    # T1
                0.001,   # tautrip2
                0.01,    # T2
                0.0      # offset
                ]   

values_factor_human_readable_6043 = [
                        1.,     # n
                        1.,     # taud1
                        1.,     # taud2
                        1.,     # F
                        1.,     # SP
                        1.,     # alpha
                        1000.,  # tautrip1 [µs]
                        1.,     # T1
                        1000.,  # tautrip2 [µs]
                        1.,     # T2
                        1.      # offset
                ]


valuestofit_6043 = [True, True, True, True, False, False, False, False, False, False, False]
parms_6043 = [labels_6043, values_6043, valuestofit_6043,
              labels_human_readable_6043, values_factor_human_readable_6043]


def MoreInfo_6043(parms, countrate=None):
    u"""Supplementary parameters:
        [9]  n₁ = n*F₁     Particle number of species 1
        [10] n₂ = n*(1-F₁) Particle number of species 2
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


model = dict()
model["Parameters"] = parms_6043
model["Definitions"] = m_gauss_3d_3d_t_t_mix_6043
model["Supplements"] = MoreInfo_6043
model["Boundaries"] = get_boundaries_3D3DTT(values_6043)
model["Constraints"] = [[2, ">", 1], [6, "<", 1], [8, "<", 6]]

Modelarray = [model]