import numpy as np

from .control import model_setup
from .cp_confocal import twod, threed
from .cp_triplet import trip
from .cp_mix import triple_pnum


def CF_Gxyz_gauss_3D3D2DT(parms, tau):
    u""" Two three-dimensional and one two-dimensional free diffusion
        with a Gaussian laser profile, including a triplet component.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        F₃ = 1-F₁-F₂
        particle1 =        F₁/( (1+τ/τ₁) * sqrt(1+τ/(τ₁*SP²)))
        particle2 = α₂₁² * F₂/( (1+τ/τ₂) * sqrt(1+τ/(τ₂*SP²)))
        particle3 = α₃₁² * F₃/( (1+τ/τ₃))
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (F₁ + α₂₁*F₂ + α₃₁*F₃)²
        G = 1/n*(particle1 + particle2 + particle3)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0]  n      Effective number of particles in confocal volume
                    (n = n₁+n₂+n₃)
        [1]  τ₁     Diffusion time of particle species 1 (3D)
        [2]  τ₂     Diffusion time of particle species 2 (3D)
        [3]  τ₃     Diffusion time of particle species 3 (2D)
        [4]  F₁     Fraction of molecules of species 1 (n₁ = n*F₁)
                    0 <= F₁ <= 1
        [5]  F₂     Fraction of molecules of species 2 (n₂ = n*F₂)
                    0 <= F₂ <= 1
        [6]  SP     SP=z₀/r₀, Structural parameter,
                    describes elongation of the confocal volume
        [7]  α₂₁    Relative molecular brightness of particle
                    2 compared to particle 1 (α = q₂/q₁)
        [8]  α₃₁    Relative molecular brightness of particle
                    3 compared to particle 1 (α = q₃/q₁)
        [9]  τ_trip Characteristic residence time in triplet state
        [10] T      Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [11] offset
        *tau* - lag time
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    taud3=parms[3]
    F1=parms[4]
    F2=parms[5]
    SP=parms[6]
    alpha21=parms[7]
    alpha31=parms[8]
    tautrip=parms[9]
    T=parms[10]
    off=parms[11]

    g = triple_pnum(n=n,
                    F1=F1,
                    F2=F2,
                    alpha21=alpha21,
                    alpha31=alpha31,
                    comp1=threed,
                    comp2=threed,
                    comp3=twod,
                    kwargs1={"tau":tau,
                             "taudiff":taud1,
                             "SP":SP},
                    kwargs2={"tau":tau,
                             "taudiff":taud2,
                             "SP":SP},
                    kwargs3={"tau":tau,
                             "taudiff":taud3},
                    )

    tr = trip(tau=tau, T=T, tautrip=tautrip)

    G = off + g*tr
    return G


def supplements(parms, countrate=None):
    u"""Supplementary parameters:
        [12]  n₁ = n*F₁     Particle number of species 1 (3D)
        [13]  n₂ = n*F₂     Particle number of species 2 (3D)
        [14]  n₃ = n*F₃     Particle number of species 3 (2D; F₃ = 1-F₁-F₂)
    """
    # We can only give you the effective particle number
    n = parms[0]
    F1 = parms[4]
    F2 = parms[5]
    Info = list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n\u2081", n*F1])
    Info.append([u"n\u2082", n*F2])
    Info.append([u"n\u2083", n*(1-F1-F2)])
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


parms = [   25,      # n
            5,       # taud1
            1000,    # taud2
            11000,   # taud3
            0.5,     # F1
            0.01,    # F2
            5,       # SP
            1.0,     # alpha21
            1.0,     # alpha31
            0.001,   # tautrip
            0.01,    # T
            0.0      # offset
            ]

## Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# F
boundaries[4] = [0,.9999999999999]
boundaries[5] = [0,.9999999999999]
# T
boundaries[10] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
             modelid=6082,
             name="Twofold 3D and one 2D diffusion with triplet (confocal)",
             comp="T+3D+3D+2D",
             mtype="Confocal (Gaussian) and triplet",
             fctn=CF_Gxyz_gauss_3D3D2DT,
             par_labels=[
                            u"n",
                            u"τ"+u"\u2081"+" [ms]",
                            u"τ"+u"\u2082"+" [ms]",
                            u"τ"+u"\u2083"+" [ms]",
                            u"F"+u"\u2081",
                            u"F"+u"\u2082",
                            u"SP",
                            u"\u03b1\u2082\u2081",
                            u"\u03b1\u2083\u2081",
                            u"τ_trip [ms]",
                            u"T",
                            u"offset"
                            ],
             par_values=parms,
             par_vary=[True, True, False, True,
                       False, True, False, False,
                       False, False, True, False],
             par_boundaries=boundaries,
             par_constraints=[[2, ">", 1], [3, ">", 2], [9, "<", 1], [5, 4, "<", "1"]],
             par_hr_labels=[
                            u"n",
                            u"τ"+u"\u2081"+" [ms]",
                            u"τ"+u"\u2082"+" [ms]",
                            u"τ"+u"\u2083"+" [ms]",
                            u"F"+u"\u2081",
                            u"F"+u"\u2082",
                            u"SP",
                            u"\u03b1\u2082\u2081",
                            u"\u03b1\u2083\u2081",
                            u"τ_trip [µs]",
                            u"T",
                            u"offset"
                            ],
             par_hr_factors=[
                            1.,     # n
                            1.,     # taud1
                            1.,     # taud2
                            1.,     # taud3
                            1.,     # F1
                            1.,     # F2
                            1.,     # SP
                            1.,     # alpha21
                            1.,     # alpha31
                            1000.,  # tautrip [µs]
                            1.,     # T
                            1.      # offset
                            ],
             supplementary_method=supplements
            )
