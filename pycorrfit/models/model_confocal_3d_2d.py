import numpy as np

from .control import model_setup
from .cp_confocal import twod, threed
from .cp_mix import double_pnum


# 3D + 2D + T
def CF_Gxyz_3d2d_gauss(parms, tau):
    u""" Two-component, two- and three-dimensional diffusion
        with a Gaussian laser profile.

        particle2D = (1-F)/ (1+τ/τ_2D) 
        particle3D = α²*F/( (1+τ/τ_3D) * sqrt(1+τ/(τ_3D*SP²)))
        norm = (1-F + α*F)²
        G = 1/n*(particle1 + particle2)/norm + offset

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
        [6] offset
        *tau* - lag time
    """
    n = parms[0]
    taud2D = parms[1]
    taud3D = parms[2]
    F = parms[3]
    SP = parms[4]
    alpha = parms[5]
    off = parms[6]

    g = double_pnum(n=n,
                    F1=1-F,
                    alpha=alpha,
                    comp1=twod,
                    comp2=threed,
                    kwargs1={"tau": tau,
                             "taudiff": taud2D},
                    kwargs2={"tau": tau,
                             "taudiff": taud3D,
                             "SP": SP},
                    )

    G = off + g
    return G


def supplements(parms, countrate=None):
    u"""Supplementary parameters:
        Effective number of freely diffusing particles in 3D solution:
        [7]  n3D = n*F
        Effective number particles diffusing on 2D surface:
        [9]  n2D = n*(1-F)
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
    0.0      # offset
]

# Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# F
boundaries[3] = [0, .9999999999999]
boundaries[-1] = [-np.inf, np.inf]


model_setup(
    modelid=6036,
    name="Separate 3D and 2D diffusion (confocal)",
    comp="3D+2D",
    mtype="Confocal (Gaussian)",
    fctn=CF_Gxyz_3d2d_gauss,
    par_labels=[
        u"n",
        u"τ_2D [ms]",
        u"τ_3D [ms]",
        u"F_3D",
        u"SP",
        u"\u03b1"+" (q_3D/q_2D)",
        u"offset"
    ],
    par_values=parms,
    par_vary=[True, True, True, True, False, False, False],
    par_boundaries=boundaries,
    par_constraints=[[2, "<", 1]],
    supplementary_method=supplements
)
