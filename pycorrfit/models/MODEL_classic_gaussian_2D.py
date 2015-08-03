# -*- coding: utf-8 -*-
"""
This file contains some simple 2D models for confocal microscopy
"""
from __future__ import division

import numpy as np


# 2D simple gauss
def CF_Gxy_gauss(parms, tau):
    u""" Two-dimensional diffusion with a Gaussian laser profile.

        G(τ) = offset + 1/( n * (1+τ/τ_diff) )
    
        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/(π*r₀²)

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal area
        [1] τ_diff  Characteristic residence time in confocal area
        [3] offset
        *tau* - lag time
    """
    n = parms[0]
    taudiff = parms[1]
    dc = parms[2]

    BB = 1 / ( (1.+tau/taudiff) )
    G = dc + 1/n * BB
    return G

def Check_xy_gauss(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1])

    return parms


# 2D simple gauss
def CF_Gxy_T_gauss(parms, tau):
    u""" Two-dimensional diffusion with a Gaussian laser profile,
        including a triplet component.
        The triplet factor takes into account a blinking term.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)

        G(τ) = offset + 1/( n * (1+τ/τ_diff) )*triplet
    
        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/(π*r₀²)

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal area
        [1] τ_diff  Characteristic residence time in confocal area
        [2] τ_trip  Characteristic residence time in triplet state
        [3] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [4] offset
        *tau* - lag time
    """
    n = parms[0]
    taudiff = parms[1]
    tautrip = parms[2]
    T = parms[3]
    dc = parms[4]

    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)

    BB = 1 / ( (1.+tau/taudiff) )
    G = dc + 1/n * BB * triplet
    return G



def Check_xy_T_gauss(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) # = taudiff
    tautrip = np.abs(parms[2])
    T=parms[3]


    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)

    parms[2] = tautrip
    parms[3] = T
    return parms



# 2D + 2D + Triplet Gauß
    # Model 6031
def CF_Gxyz_gauss_2D2DT(parms, tau):
    u""" Two-component, two-dimensional diffusion with a Gaussian laser
        profile, including a triplet component.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle1 = F₁/(1+τ/τ₁)
        particle2 = α*(1-F₁)/(1+τ/τ₂)
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (F₁ + α*(1-F₁))²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal area
                    (n = n₁+n₂)
        [1] τ₁      Diffusion time of particle species 1
        [2] τ₂      Diffusion time of particle species 2
        [3] F₁      Fraction of molecules of species 1 (n₁ = n*F₁)
                    0 <= F₁ <= 1
        [4] α       Relative molecular brightness of particle 2
                    compared to particle 1 (α = q₂/q₁)
        [5] τ_trip  Characteristic residence time in triplet state
        [6] T       Fraction of particles in triplet (non-fluorescent)
                    state 0 <= T < 1
        [7] offset
        *tau* - lag time
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    F=parms[3]
    alpha=parms[4]
    tautrip=parms[5]
    T=parms[6]
    off=parms[7]

    particle1 = F/( 1+tau/taud1 )
    particle2 = alpha**2*(1-F)/( 1+tau/taud2 )
    # If the fraction of dark molecules is zero, we put the
    # whole triplet fraction to death.
    triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)
    # For alpha == 1, *norm* becomes one
    norm = (F + alpha*(1-F))**2

    G = 1/n*(particle1 + particle2)*triplet/norm + off
    return G

def Check_6031(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) # = taud1
    parms[2] = np.abs(parms[2]) # = taud2
    F=parms[3]
    parms[4] = np.abs(parms[4])
    tautrip = np.abs(parms[5])
    T=parms[6]
    #off=parms[7]
    
     
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[5] = tautrip
    parms[6] = T

    return parms


def MoreInfo_6001(parms, countrate=None):
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info
    
    
def MoreInfo_6031(parms, countrate=None):
    u"""Supplementary parameters:
        [8] n₁ = n*F₁     Particle number of species 1
        [9] n₂ = n*(1-F₁) Particle number of species 2
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


# 2D Model Gauss
m_twodga6001 = [6001, u"2D", u"2D confocal diffusion", CF_Gxy_gauss]
labels_6001 = [u"n",
               u"τ_diff [ms]",
               u"offset"]
values_6001 = [4.0, 0.4, 0.0]
valuestofit_6001 = [True, True, False]
parms_6001 = [labels_6001, values_6001, valuestofit_6001]


# 2D Model Gauss with Triplet
m_twodga6002 = [6002, u"T+2D", u"2D confocal diffusion with triplet", 
                CF_Gxy_T_gauss]
labels_6002 = [u"n",
               u"τ_diff [ms]",
               u"τ_trip [ms]",
               u"T",
               u"offset"]
values_6002 = [4.0, 0.4, 0.001, 0.01, 0.0]
labels_hr_6002 = [u"n",
                  u"τ_diff [ms]",
                  u"τ_trip [µs]",
                  u"T",
                  u"offset"]
factors_hr_6002 = [1., 1., 1000., 1., 1.]
valuestofit_6002 = [True, True, True, True, False]
parms_6002 = [labels_6002, values_6002, valuestofit_6002,
              labels_hr_6002, factors_hr_6002]


# 2D + 2D + T model gauss
m_gauss_2d_2d_t_mix_6031 = [6031, u"T+2D+2D",
                            u"Separate 2D diffusion + triplet, Gauß",
                            CF_Gxyz_gauss_2D2DT]
labels_6031  = ["n",
                u"τ"+u"\u2081"+u" [ms]",
                u"τ"+u"\u2082"+u" [ms]",
                u"F"+u"\u2081", 
                u"\u03b1"+u" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                u"τ_trip [ms]",
                u"T",
                u"offset"
                ]
values_6031 = [ 
                25,      # n
                5,       # taud1
                1000,    # taud2
                0.5,     # F
                1.0,     # alpha
                0.001,   # tautrip
                0.01,    # T
                0.0      # offset
                ]        
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6031  = [
                        u"n",
                        u"τ"+u"\u2081"+u" [ms]",
                        u"τ"+u"\u2082"+u" [ms]",
                        u"F"+u"\u2081", 
                        u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                        u"τ_trip [µs]",
                        u"T",
                        u"offset"
                            ]
values_factor_human_readable_6031 = [
                1.,     # "n",
                1.,     # "τ"+u"\u2081"+" [ms]",
                1.,     # "τ"+u"\u2082"+" [ms]",
                1.,     # "F"+u"\u2081", 
                1.,     # u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                1000.,  # "τ_trip [µs]",
                1.,     # "T",
                1.      # "offset"
                ]
valuestofit_6031 = [True, True, True, True, False, False, False, False]
parms_6031 = [labels_6031, values_6031, valuestofit_6031,
              labels_human_readable_6031, values_factor_human_readable_6031]


model1 = dict()
model1["Parameters"] = parms_6001
model1["Definitions"] = m_twodga6001
model1["Supplements"] = MoreInfo_6001
model1["Verification"] = Check_xy_gauss

model2 = dict()
model2["Parameters"] = parms_6002
model2["Definitions"] = m_twodga6002
model2["Supplements"] = MoreInfo_6001
model2["Verification"] = Check_xy_T_gauss

model3 = dict()
model3["Parameters"] = parms_6031
model3["Definitions"] = m_gauss_2d_2d_t_mix_6031
model3["Supplements"] = MoreInfo_6031
model3["Verification"] = Check_6031


Modelarray = [model1, model2, model3]
