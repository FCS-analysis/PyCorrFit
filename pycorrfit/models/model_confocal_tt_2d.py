import numpy as np

from .control import model_setup
from .cp_confocal import twod
from .cp_triplet import trip


# 2D + TT Gauß
# Model 6003
def CF_Gxy_gauss_2DTT(parms, tau):
    u""" Two-dimensional free diffusion
        with a Gaussian laser profile, including two triplet components.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle = 1/(1+τ/τ_diff)
        triplet1 = 1 + T₁/(1-T₁)*exp(-τ/τ_trip₁)
        triplet2 = 1 + T₂/(1-T₂)*exp(-τ/τ_trip₂)
        G = 1/n*particle*triplet1*triplet2 + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0]  n        Effective number of particles in confocal volume
        [1]  τ_diff   Diffusion time of particle
        [2]  τ_trip₁  Characteristic residence time in triplet state
        [3]  T₁       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [4]  τ_trip₂  Characteristic residence time in triplet state
        [5]  T₂       Fraction of particles in triplet (non-fluorescent) state
                      0 <= T < 1
        [6]  offset
        *tau* - lag time
    """
    n = parms[0]
    taud = parms[1]
    tautrip1 = parms[2]
    T1 = parms[3]
    tautrip2 = parms[4]
    T2 = parms[5]
    off = parms[6]

    g = twod(tau=tau, taudiff=taud)

    tr1 = trip(tau=tau, T=T1, tautrip=tautrip1)
    tr2 = trip(tau=tau, T=T2, tautrip=tautrip2)

    G = off + 1/n * g * tr1 * tr2

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


parms = [
    4,       # n
    .4,      # taud
    0.001,   # tautrip1
    0.01,    # T1
    0.002,   # tautrip2
    0.01,    # T2
    0.0      # offset
]

# Boundaries
# strictly positive
boundaries = [[0, np.inf]]*len(parms)
# T
boundaries[3] = [0, .9999999999999]
boundaries[5] = [0, .9999999999999]
# offset
boundaries[-1] = [-np.inf, np.inf]


model_setup(
    modelid=6003,
    name="2D diffusion with double triplet (confocal)",
    comp="T+T+2D",
    mtype="Confocal (Gaussian) with double triplet",
    fctn=CF_Gxy_gauss_2DTT,
    par_labels=[
        u"n",
        u"τ_diff [ms]",
        u"τ_trip₁ [ms]",
        u"T₁",
        u"τ_trip₂ [ms]",
        u"T₂",
        u"offset"
    ],
    par_values=parms,
    par_vary=[True, True, False, False, False, False, False],
    par_boundaries=boundaries,
    par_constraints=[[2, "<", 1], [4, ">", 2]],
    par_hr_labels=[
        u"n",
        u"τ_diff [ms]",
        u"τ_trip₁ [µs]",
        u"T₁",
        u"τ_trip₂ [µs]",
        u"T₂",
        u"offset"
    ],
    par_hr_factors=[
        1.,     # n
        1.,     # taudiff
        1000.,  # tautrip1 [µs]
        1.,     # T1
        1000.,  # tautrip2 [µs]
        1.,     # T2
        1.      # offset
    ],
    supplementary_method=supplements
)
