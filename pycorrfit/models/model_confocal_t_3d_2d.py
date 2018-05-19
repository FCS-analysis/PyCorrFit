import numpy as np

from .control import model_setup
from .cp_confocal import twod, threed
from .cp_triplet import trip
from .cp_mix import double_pnum


# 3D + 2D + T
def CF_Gxyz_3d2dT_gauss(parms, tau):
    u""" Two-component, two- and three-dimensional diffusion
        with a Gaussian laser profile, including a triplet component.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle2D = (1-F)/ (1+τ/τ_2D) 
        particle3D = α²*F/( (1+τ/τ_3D) * sqrt(1+τ/(τ_3D*SP²)))
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (1-F + α*F)²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
                    (n = n2D+n3D)
        [1] τ_2D    Diffusion time of surface bound particls
        [2] τ_3D    Diffusion time of freely diffusing particles
        [3] F       Fraction of molecules of the freely diffusing species
                    (n3D = n*F), 0 <= F <= 1
        [4] SP      SP=z₀/r₀ Structural parameter,
                         describes elongation of the confocal volume
        [5] α       Relative molecular brightness of particle
                    3D compared to particle 2D (α = q3D/q2D)
        [6] τ_trip  Characteristic residence time in triplet state
        [7] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [8] offset
        *tau* - lag time
    """
    n=parms[0]
    taud2D=parms[1]
    taud3D=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip=parms[6]
    T=parms[7]
    off=parms[8]

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

    tr = trip(tau=tau, T=T, tautrip=tautrip)

    G = off + g*tr
    return G

def supplements(parms, countrate=None):
    u"""Supplementary parameters:
        Effective number of freely diffusing particles in 3D solution:
        [9]  n3D = n*F
        Effective number particles diffusing on 2D surface:
        [10] n2D = n*(1-F)
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
            7,       # SP
            1.0,     # alpha
            0.001,   # tautrip
            0.01,    # T
            0.0      # offset
            ] 

## Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# F
boundaries[3] = [0,.9999999999999]
# T
boundaries[7] = [0,.9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
             modelid=6032,
             name="Separate 3D and 2D diffusion with triplet (confocal)",
             comp="T+3D+2D",
             mtype="Confocal (Gaussian) and triplet",
             fctn=CF_Gxyz_3d2dT_gauss,
             par_labels=[
                            u"n",
                            u"τ_2D [ms]",
                            u"τ_3D [ms]",
                            u"F_3D", 
                            u"SP",
                            u"\u03b1"+" (q_3D/q_2D)", 
                            u"τ_trip [ms]",
                            u"T",
                            u"offset"
                            ],
             par_values=parms,
             par_vary=[True, True, True, True, False, False, False, False, False],
             par_boundaries=boundaries,
             par_constraints=[[2, "<", 1], [6, "<", 2]],
             par_hr_labels=[
                            u"n",
                            u"τ_2D [ms]",
                            u"τ_3D [ms]",
                            u"F_3D", 
                            u"SP",
                            u"\u03b1"+" (q_3D/q_2D)", 
                            u"τ_trip [µs]",
                            u"T",
                            u"offset"
                            ],
             par_hr_factors=[
                              1.,     # "n",
                              1.,     # "τ_2D [ms]",
                              1.,     # "τ_3D [ms]",
                              1.,     # "F_3D", 
                              1.,     # "SP",
                              1.,     # u"\u03b1"+" (q_3D/q_2D)", 
                              1000.,  # "τ_trip [µs]",
                              1.,     # "T",
                              1.      # "offset"
                            ],
             supplementary_method=supplements
            )
