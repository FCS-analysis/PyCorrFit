# -*- coding: utf-8 -*-
"""
This file contains TIR one component models + triplet
"""
from __future__ import division

import numpy as np

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

    BB = 1 / ( (1.+tau/taudiff) * np.sqrt(1.+tau/(SP**2*taudiff)) )
    G = off + 1/n * BB
    return G


# 3D blinking gauss
    # Model 6011
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

    if tautrip == 0 or T == 0:
        AA = 1
    else:
        AA = 1 + T/(1-T) * np.exp(-tau/tautrip)

    BB = 1 / ( (1+tau/taudiff) * np.sqrt(1+tau/(SP**2*taudiff)) )
    G = off + 1/n * AA * BB
    return G


def Check_6011(parms):
    parms[0] = np.abs(parms[0])
    T = parms[1]
    tautrip = np.abs(parms[2])
    parms[3] = np.abs(parms[3])# = taudiff
    parms[4] = np.abs(parms[4])
    #off = parms[5]
    
    # Triplet fraction is between 0 and one.
    T = (0.<=T<1.)*T + .999999999*(T>=1)

    parms[1] = T
    parms[2] = tautrip

    return parms


# 3D + 3D + Triplet Gauß
    # Model 6030
def CF_Gxyz_gauss_3D3DT(parms, tau):
    u""" Two-component three-dimensional free diffusion
        with a Gaussian laser profile, including a triplet component.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle1 = F₁/( (1+τ/τ₁) * sqrt(1+τ/(τ₁*SP²)))
        particle2 = α*(1-F₁)/( (1+τ/τ₂) * sqrt(1+τ/(τ₂*SP²)))
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (F₁ + α*(1-F₁))²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
                    (n = n₁+n₂)
        [1] τ₁      Diffusion time of particle species 1
        [2] τ₂      Diffusion time of particle species 2
        [3] F₁      Fraction of molecules of species 1 (n₁ = n*F₁)
                    0 <= F₁ <= 1
        [4] SP      SP=z₀/r₀, Structural parameter,
                    describes elongation of the confocal volume
        [5] α       Relative molecular brightness of particle
                    2 compared to particle 1 (α = q₂/q₁)
        [6] τ_trip  Characteristic residence time in triplet state
        [7] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [8] offset
        *tau* - lag time
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip=parms[6]
    T=parms[7]
    off=parms[8]

    particle1 = F/( (1+tau/taud1) * np.sqrt(1+tau/(taud1*SP**2)))
    particle2 = alpha**2*(1-F)/( (1+tau/taud2) * np.sqrt(1+tau/(taud2*SP**2)))
    # If the fraction of dark molecules is zero.
    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)
    # For alpha == 1, *norm* becomes one
    norm = (F + alpha*(1-F))**2

    G = 1/n*(particle1 + particle2)*triplet/norm + off
    return G

def Check_3D3DT(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) # = taud1
    parms[2] = np.abs(parms[2]) # = taud2
    F=parms[3]
    parms[4]=np.abs(parms[4])
    parms[5]=np.abs(parms[5])
    tautrip=np.abs(parms[6])
    T=parms[7]
    #off=parms[8]
    
    
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[6] = tautrip
    parms[7] = T

    return parms


def MoreInfo_1C(parms, countrate=None):
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


def MoreInfo_6030(parms, countrate=None):
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


# 3D Model blink gauss
m_3dblink6011 = [6011, "T+3D","3D confocal diffusion with triplet", 
                 CF_Gxyz_blink]
labels_6011 = [u"n",
               u"T",
               u"τ_trip [ms]",
               u"τ_diff [ms]",
               u"SP",
               u"offset"]
values_6011 = [4.0, 0.2, 0.001, 0.4, 5.0, 0.0]
labels_hr_6011 = [u"n",
                  u"T",
                  u"τ_trip [µs]",
                  u"τ_diff [ms]",
                  u"SP",
                  u"offset"]
factors_hr_6011 = [1., 1., 1000., 1., 1., 1.]
valuestofit_6011 = [True, True, True, True, False, False]
parms_6011 = [labels_6011, values_6011, valuestofit_6011,
              labels_hr_6011, factors_hr_6011]

# 3D Model gauss
m_3dgauss6012 = [6012, "3D","3D confocal diffusion", CF_Gxyz_gauss]
labels_6012 = [u"n",
               u"τ_diff [ms]",
               u"SP",
               u"offset"]
values_6012 = [4.0, 0.4, 5.0, 0.0]
valuestofit_6012 = [True, True, False, False]
parms_6012 = [labels_6012, values_6012, valuestofit_6012]

# 3D + 3D + T model gauss
m_gauss_3d_3d_t_mix_6030 = [6030, "T+3D+3D",
                            u"Separate 3D diffusion + triplet, Gauß",
                            CF_Gxyz_gauss_3D3DT]
labels_6030  = [u"n",
                u"τ"+u"\u2081"+" [ms]",
                u"τ"+u"\u2082"+" [ms]",
                u"F"+u"\u2081", 
                u"SP",
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                u"τ_trip [ms]",
                u"T",
                u"offset"
                ]
values_6030 = [ 
                25,      # n
                5,       # taud1
                1000,    # taud2
                0.5,     # F
                5,       # SP
                1.0,     # alpha
                0.001,   # tautrip
                0.01,    # T
                0.0      # offset
                ]        
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6030  = [
                        u"n",
                        u"τ"+u"\u2081"+" [ms]",
                        u"τ"+u"\u2082"+" [ms]",
                        u"F"+u"\u2081", 
                        u"SP",
                        u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                        u"τ_trip [µs]",
                        u"T",
                        u"offset"
                            ]
values_factor_human_readable_6030 = [
                        1.,     # n
                        1.,     # taud1
                        1.,     # taud2
                        1.,     # F
                        1.,     # SP
                        1.,     # alpha
                        1000.,  # tautrip [µs]
                        1.,     # T
                        1.      # offset
                ]
valuestofit_6030 = [True, True, True, True, False, False, False, False, False]
parms_6030 = [labels_6030, values_6030, valuestofit_6030,
              labels_human_readable_6030, values_factor_human_readable_6030]


# Pack the models
model1 = dict()
model1["Parameters"] = parms_6011
model1["Definitions"] = m_3dblink6011
model1["Supplements"] = MoreInfo_1C
model1["Verification"] = Check_6011

model2 = dict()
model2["Parameters"] = parms_6012
model2["Definitions"] = m_3dgauss6012
model2["Supplements"] = MoreInfo_1C

model3 = dict()
model3["Parameters"] = parms_6030
model3["Definitions"] = m_gauss_3d_3d_t_mix_6030
model3["Supplements"] = MoreInfo_6030
model3["Verification"] = Check_3D3DT


Modelarray = [model1, model2, model3]
