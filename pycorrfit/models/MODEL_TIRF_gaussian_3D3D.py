# -*- coding: utf-8 -*-
""" 
This file contains a 3D+3D+T TIR FCS model.
"""
from __future__ import division

import numpy as np
import scipy.special as sps


def wixi(x):
    """ Complex Error Function (Faddeeva/Voigt).
        w(i*x) = exp(x**2) * ( 1-erf(x) )
        This function is called by other functions within this module.
        We are using the scipy.special.wofz module which calculates
        w(z) = exp(-z**2) * ( 1-erf(-iz) )
        z = i*x
    """
    z = x*1j
    wixi = sps.wofz(z)
    # We should have a real solution. Make sure nobody complains about
    # some zero-value imaginary numbers.
    
    return np.real_if_close(wixi)  

# 3D + 3D + T
def CF_Gxyz_3D3DT_gauss(parms, tau):
    u""" Two-component three-dimensional diffusion with a Gaussian
        lateral detection profile and an exponentially decaying profile
        in axial direction, including a triplet component.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        w(i*x) = exp(x²)*erfc(x)
        taud1 = r₀²/(4*D₁)
        κ = 1/d_eva
        x1 = sqrt(D₁*τ)*κ
        gz1 = κ * [ sqrt(D₁*τ/π) + (1 - 2*D₁*τ*κ)/(2*κ) * w(i*x1) ]
        g2D1 = 1 / [ 1+τ/taud1 ]
        particle1 = F₁ * g2D1 * gz1

        taud2 = r₀²/(4*D₂)
        x2 = sqrt(D₂*τ)*κ
        gz2 = κ * [ sqrt(D₂*τ/π) + (1 - 2*D₂*τ*κ)/(2*κ) * w(i*x2) ]
        g2D2 = 1 / [ 1+τ/taud2 ]
        particle2 =  α*(1-F₁) * g2D2 * gz2


        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (1-F₁ + α*F₁)²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
                    (n = n₁+n₂)
        [1] D₁      Diffusion coefficient of species 1
        [2] D₂      Diffusion coefficient of species 2
        [3] F₁      Fraction of molecules of species 1 (n₁ = n*F₁)
                    0 <= F₁ <= 1
        [4] r₀      Lateral extent of the detection volume
        [5] d_eva   Evanescent field depth
        [6] α       Relative molecular brightness of particle
                    2 compared to particle 1 (α = q₂/q₁)
        [7] τ_trip  Characteristic residence time in triplet state
        [8] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [9] offset
        *tau* - lag time
    """
    n=parms[0]
    D1=parms[1]
    D2=parms[2]
    F=parms[3]
    r0=parms[4]
    deva=parms[5]
    alpha=parms[6]
    tautrip=parms[7]
    T=parms[8]
    off=parms[9]

    kappa = 1/deva


    ### 1st species
    tauD1 = r0**2/(4*D1)
    # 2D gauss component
    g2D1 = 1 / ( (1.+tau/tauD1) )
    # 1d TIR component
    # Axial correlation    
    x1 = np.sqrt(D1*tau)*kappa
    w_ix1 = wixi(x1)
    # Gz = 1/N1D * gz = kappa / Conc.1D * gz
    gz1 = kappa * (np.sqrt(D1*tau/np.pi) -
                   (2*D1*tau*kappa**2 - 1)/(2*kappa) * w_ix1)
    particle1 = F * g2D1 * gz1

    ### 2nd species
    tauD2 = r0**2/(4*D2)
    # 2D gauss component
    g2D2 = 1 / ( (1.+tau/tauD2) )
    # 1d TIR component
    # Axial correlation    
    x2 = np.sqrt(D2*tau)*kappa
    w_ix2 = wixi(x2)
    # Gz = 1/N1D * gz = kappa / Conc.1D * gz
    gz2 = kappa * (np.sqrt(D2*tau/np.pi) -
                   (2*D2*tau*kappa**2 - 1)/(2*kappa) * w_ix2)
    particle2 = alpha**2*(1-F) * g2D2 * gz2

    ### triplet
    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)

    ### Norm
    norm = (F + alpha*(1-F))**2

    ### Correlation function
    G = 1/n*(particle1 + particle2)*triplet/norm
    return G + off


def Checkme(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) # = D1
    parms[2] = np.abs(parms[2]) # = D2
    F=parms[3]
    parms[4] = np.abs(parms[4]) # = r0
    parms[5]=np.abs(parms[5])
    parms[6]=np.abs(parms[6])
    tautrip=np.abs(parms[7])
    T=parms[8]
    #off=parms[9]

    # REMOVED (issue #2)
    ## Force triplet component to be smaller than diffusion times
    #tauD2 = r0**2/(4*D2)
    #tauD1 = r0**2/(4*D1)
    #tautrip = min(tautrip,tauD2*0.9, tauD1*0.9)

    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[7] = tautrip
    parms[8] = T

    return parms


def MoreInfo(parms, countrate=None):
    u"""Supplementary parameters:
        Effective number of particle species 1:
        [10] n₁ = n*F₁
        Effective number of particle species 2:
        [11] n₂ = n*(1-F₁)
        Value of the correlation function at lag time zero:
        [12] G(0)
        Effective measurement volume:
        [13] V_eff [al] = π * r₀² * d_eva
        Concentration of particle species 1:
        [14] C₁ [nM] = n₁/V_eff
        Concentration of particle species 2:
        [15] C₂ [nM] = n₂/V_eff
    """
    # We can only give you the effective particle number
    n=parms[0]
    #D1=parms[1]
    #D2=parms[2]
    F=parms[3]
    r0=parms[4]
    deva=parms[5]
    #alpha=parms[6]

    Info=list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n\u2081", n*F])
    Info.append([u"n\u2082", n*(1.-F)])
    # Detection area:
    Veff = np.pi * r0**2 * deva
    C1 = n*F / Veff
    C2 = n*(1-F) / Veff
    # Correlation function at tau = 0
    G_0 = CF_Gxyz_3D3DT_gauss(parms, 0)
    Info.append(["G(0)", G_0])
    Info.append(["V_eff [al]", Veff])
    Info.append(["C"+u"\u2081"+" [nM]", C1 * 10000/6.0221415])
    Info.append(["C"+u"\u2082"+" [nM]", C2 * 10000/6.0221415])

    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


# 3D + 3D + T model gauss
m_gauss_3d_3d_t = [6034, "T+3D+3D",
                            "Combined 3D diffusion + triplet w/ TIR",
                            CF_Gxyz_3D3DT_gauss]
labels  = [u"n",
           u"D"+u"\u2081"+u" [10 µm²/s]",
           u"D"+u"\u2082"+u" [10 µm²/s]",
           u"F"+u"\u2081", 
           u"r₀ [100 nm]",
           u"d_eva [100 nm]",
           u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
           u"τ_trip [ms]",
           u"T",
           u"offset"
                ]
values = [ 
                25,      # n
                25.,       # D1
                0.9,    # D2
                0.5,     # F1
                9.44,       # r0
                1.0,       # deva
                1.0,     # alpha
                0.001,       # tautrip
                0.01,       # T
                0.0      # offset
                ]    
# Human readable stuff
labelshr  = [   u"n",
                u"D"+u"\u2081"+u" [µm²/s]",
                u"D"+u"\u2082"+u" [µm²/s]",
                u"F"+u"\u2081", 
                u"r₀ [nm]",
                u"d_eva [nm]",
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                u"τ_trip [µs]",
                u"T",
                u"offset"
                ]
valueshr = [ 
                1.,      # n
                10.,       # D1
                10.,    # D2
                1.,     # F1
                100.,       # r0
                100.,       # deva
                1.,     # alpha
                1000.,       # tautrip
                1.,       # T
                1.      # offset
                ]   
    
valuestofit = [True, True, True, True, False, False, False, False, False, False]
parms = [labels, values, valuestofit, labelshr, valueshr]


model1 = dict()
model1["Parameters"] = parms
model1["Definitions"] = m_gauss_3d_3d_t
model1["Verification"] = Checkme
model1["Supplements"] = MoreInfo

Modelarray = [model1]
