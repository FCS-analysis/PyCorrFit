# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np

from .control import model_setup
from .cp_confocal import threed

# 3D simple gauss
def CF_Gxyz_gauss(parms, tau):
    # Model 6012
    u""" Three-dimanesional free diffusion with a Gaussian laser profile
        (eliptical).

        G(τ) = offset + 1/( n*(1+τ/τ_diff) * sqrt(1 + τ/(SP²*τ_diff)) )

        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/( sqrt(π³)*r₀²*z₀ )

            r₀   lateral detection radius (waist of lateral gaussian)
            z₀   axial detection length (waist of axial gaussian)
            D    Diffusion coefficient
            Conc Concentration of dye

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
        [1] τ_diff  Characteristic residence time in confocal volume
        [2] SP      SP=z₀/r₀ Structural parameter,
                    describes the axis ratio of the confocal volume
        [3] offset
        *tau* - lag time
    """
    n = parms[0]
    taudiff = parms[1]
    SP = parms[2]
    off = parms[3]

    BB = threed(tau, taudiff, SP)
    
    G = off + 1/n * BB
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


parms = [4.0, 0.4, 5.0, 0.0]
boundaries = [[0, np.inf]]*len(parms)
boundaries[-1] = [-np.inf, np.inf]

model_setup(
             modelid=6012,
             name="3D diffusion (confocal)",
             comp="3D",
             mtype="Confocal (Gaussian)",
             fctn=CF_Gxyz_gauss,
             par_labels=[
                            u"n",
                            u"τ_diff [ms]",
                            u"SP",
                            u"offset"],
             par_values=parms,
             par_vary=[True, True, False, False],
             par_boundaries=boundaries,
             supplementary_method=supplements
            )
