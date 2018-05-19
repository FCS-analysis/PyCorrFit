import numpy as np

from .control import model_setup
from .cp_confocal import twod, threed
from .cp_triplet import trip
from .cp_mix import double_pnum


# 3D + 2D + TT Gauß
# Model 6045
def CF_Gxyz_gauss_3D2DTT(parms, tau):
    u""" Two-component three-dimensional free diffusion
        with a Gaussian laser profile, including two triplet components.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle2D = (1-F)/ (1+τ/τ_2D) 
        particle3D = α²*F/( (1+τ/τ_3D) * sqrt(1+τ/(τ_3D*SP²)))
        triplet1 = 1 + T₁/(1-T₁)*exp(-τ/τ_trip₁)
        triplet2 = 1 + T₂/(1-T₂)*exp(-τ/τ_trip₂)
        norm = (F₁ + α*(1-F₁))²
        G = 1/n*(particle2D + particle3D)*triplet1*triplet2/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n         Effective number of particles in confocal volume
                      (n = n2D+n3D)
        [1] τ_2D      Diffusion time of surface bound particls
        [2] τ_3D      Diffusion time of freely diffusing particles
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
    taud2D=parms[1]
    taud3D=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip1=parms[6]
    T1=parms[7]
    tautrip2=parms[8]
    T2=parms[9]
    off=parms[10]

    g = double_pnum(n=n,
                    F1=1-F,
                    alpha=alpha,
                    comp1=twod,
                    comp2=threed,
                    kwargs1={"tau":tau,
                             "taudiff":taud2D},
                    kwargs2={"tau":tau,
                             "taudiff":taud3D,
                             "SP":SP},
                    )

    tr1 = trip(tau=tau, T=T1, tautrip=tautrip1)
    tr2 = trip(tau=tau, T=T2, tautrip=tautrip2)

    G = off + g * tr1 * tr2

    return G


def supplements(parms, countrate=None):
    u"""Supplementary parameters:
        Effective number of freely diffusing particles in 3D solution:
        [11] n3D = n*F
        Effective number particles diffusing on 2D surface:
        [12] n2D = n*(1-F)
    """
    # We can only give you the effective particle number
    n = parms[0]
    F3d = parms[3]
    Info = list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n3D", n*F3d])
    Info.append([u"n2D", n*(1.-F3d)])
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append([u"cpp [kHz]", cpp])
    return Info    
    

parms = [
            25,      # n
            240,     # taud2D
            0.1,     # taud3D
            0.5,     # F3D
            5,       # SP
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
boundaries[7] = [0,.9999999999999]
boundaries[9] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
             modelid=6045,
             name="Separate 3D and 2D diffusion with double triplet (confocal)",
             comp="T+T+3D+2D",
             mtype="Confocal (Gaussian) with double triplet",
             fctn=CF_Gxyz_gauss_3D2DTT,
             par_labels=[
                            u"n",
                            u"τ_2D [ms]",
                            u"τ_3D [ms]",
                            u"F_3D", 
                            u"SP",
                            u"\u03b1"+" (q_3D/q_2D)", 
                            u"τ_trip₁ [ms]",
                            u"T₁",
                            u"τ_trip₂ [ms]",
                            u"T₂",
                            u"offset"
                            ],
             par_values=parms,
             par_vary=[True, True, True, True, False, False, False, False, False, False, False],
             par_boundaries=boundaries,
             par_constraints=[[2, "<", 1], [6, "<", 2], [8, ">", 6]],
             par_hr_labels=[
                            u"n",
                            u"τ_2D [ms]",
                            u"τ_3D [ms]",
                            u"F_3D", 
                            u"SP",
                            u"\u03b1"+" (q_3D/q_2D)", 
                            u"τ_trip₁ [µs]",
                            u"T₁",
                            u"τ_trip₂ [µs]",
                            u"T₂",
                            u"offset"
                            ],
             par_hr_factors=[
                            1.,     # n
                            1.,     # "τ_2D [ms]",
                            1.,     # "τ_3D [ms]",
                            1.,     # "F_3D", 
                            1.,     # "SP",
                            1.,     # u"\u03b1"+" (q_3D/q_2D)", 
                            1000.,  # tautrip1 [µs]
                            1.,     # T1
                            1000.,  # tautrip2 [µs]
                            1.,     # T2
                            1.      # offset
                            ],
             supplementary_method=supplements
            )
