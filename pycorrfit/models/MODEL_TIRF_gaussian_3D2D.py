# -*- coding: utf-8 -*-
"""
This file contains a 3D+2D+T TIR FCS model.
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

# 3D + 2D + T
def CF_Gxyz_3d2dT_gauss(parms, tau):
    u""" Two-component, two- and three-dimensional diffusion
        with a Gaussian lateral detection profile and
        an exponentially decaying profile in axial direction,
        including a triplet component.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        kappa = 1/d_eva
        x = sqrt(D_3D*τ)*kappa
        w(i*x) = exp(x²)*erfc(x)
        gz = kappa * 
             [ sqrt(D_3D*τ/pi) + (1 - 2*D_3D*τ*kappa²)/(2*kappa) * w(i*x) ]
        g2D3D = 1 / [ 1+4*D_3D*τ/r₀² ]
        particle3D = α*F * g2D3D * gz
        particle2D = (1-F)/ (1+4*D_2D*τ/r₀²) 
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (1-F + α*F)²
        G = 1/n*(particle2D + particle3D)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
                    (n = n2D+n3D)
        [1] D_2D    Diffusion coefficient  of surface bound particles
        [2] D_3D    Diffusion coefficient of freely diffusing particles
        [3] F       Fraction of molecules of the freely diffusing species
                    (n3D = n*F), 0 <= F <= 1
        [4] r₀      Lateral extent of the detection volume
        [5] d_eva   Evanescent field depth
        [6] α       Relative molecular brightness of freely diffusing
                    compared to surface bound particles (α = q3D/q2D)
        [7] τ_trip  Characteristic residence time in triplet state
        [8] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [9] offset
        *tau* - lag time
    """
    n=parms[0]
    D2D=parms[1]
    D3D=parms[2]
    F=parms[3]
    r0=parms[4]
    deva=parms[5]
    alpha=parms[6]
    tautrip=parms[7]
    T=parms[8]
    off=parms[9]

    ### 2D species
    taud2D = r0**2/(4*D2D)
    particle2D = (1-F)/ (1+tau/taud2D) 

    ### 3D species
    taud3D = r0**2/(4*D3D)
    # 2D gauss component
    g2D3D = 1 / ( (1.+tau/taud3D) )
    # 1d TIR component
    # Axial correlation    
    kappa = 1/deva
    x = np.sqrt(D3D*tau)*kappa
    w_ix = wixi(x)
    # Gz = 1/N1D * gz = kappa / Conc.1D * gz
    gz = kappa * (np.sqrt(D3D*tau/np.pi) - 
         (2*D3D*tau*kappa**2 - 1)/(2*kappa) * w_ix)
    particle3D = alpha**2*F * g2D3D * gz

    ### triplet
    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)

    ### Norm
    norm = (1-F + alpha*F)**2

    ### Correlation function
    G = 1/n*(particle2D + particle3D)*triplet/norm
    return G + off


def Checkme(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) # = D2D
    parms[2] = np.abs(parms[2]) # = D3D
    F=parms[3]
    parms[4] = np.abs(parms[4]) # = r0
    parms[5]=np.abs(parms[5])
    parms[6]=np.abs(parms[6])
    tautrip=np.abs(parms[7])
    T=parms[8]
    #off=parms[9]

    #taud2D = r0**2/(4*D2D)
    #taud3D = r0**2/(4*D3D)
    # We are not doing this anymore (Issue #2).
    ## Force triplet component to be smaller than diffusion times
    ## tautrip = min(tautrip,taud2D*0.9, taud3D*0.9)
    
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
        Effective number of freely diffusing particles in 3D:
        [10] n3D = n*F
        Effective number particles diffusing on 2D surface:
        [11] n2D = n*(1-F)
        Value of the correlation function at lag time zero:
        [12] G(0)
        Effective measurement volume:
        [13] V_eff [al] = π * r₀² * d_eva
        Concentration of the 2D species:
        [14] C_2D [1/µm²] = n2D / ( π * r₀² )
        Concentration of the 3D species:
        [15] C_3D [nM] = n3D/V_eff
    """
    # We can only give you the effective particle number
    n=parms[0]
    #D2D=parms[1]
    #D3D=parms[2]
    F=parms[3]
    r0=parms[4]
    deva=parms[5]
    #alpha=parms[6]

    Info=list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n3D", n*F])
    Info.append([u"n2D", n*(1.-F)])
    # Detection area:
    Veff = np.pi * r0**2 * deva
    C3D = n*F / Veff
    C2D = n*(1-F) / ( np.pi*r0**2 )
    # Correlation function at tau = 0
    G_0 = CF_Gxyz_3d2dT_gauss(parms, 0)
    Info.append([u"G(0)", G_0])
    Info.append([u"V_eff [al]", Veff])
    Info.append([u"C_2D [1/µm²]", C2D * 100])
    Info.append([u"C_3D [nM]", C3D * 10000/6.0221415])

    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append([u"cpp [kHz]", cpp])
    return Info


# 3D + 3D + T model gauss
m_gauss_3d_2d_t = [6033, "T+3D+2D",
                            "Separate 3D and 2D diffusion + triplet w/ TIR",
                            CF_Gxyz_3d2dT_gauss]
labels  = [ u"n",
            u"D_2D [10 µm²/s]",
            u"D_3D [10 µm²/s]",
            u"F_3D", 
            u"r₀ [100 nm]",
            u"d_eva [100 nm]",
            u"\u03b1"+" (q_3D/q_2D)", 
            u"τ_trip [ms]",
            u"T",
            u"offset"
                ]
values = [ 
                25,      # n
                0.51,       # D2D
                25.1,    # D3D
                0.45,     # F3D
                9.44,       # r0
                1.0,       # deva
                1.0,     # alpha
                0.001,       # tautrip
                0.01,       # T
                0.0      # offset
                ]  
# Human readable stuff
labelshr  = [u"n",
             u"D_2D [µm²/s]",
             u"D_3D [µm²/s]",
             u"F_3D", 
             u"r₀ [nm]",
             u"d_eva [nm]",
             u"\u03b1"+" (q_3D/q_2D)", 
             u"τ_trip [µs]",
             u"T",
             u"offset"
                ] 
valueshr = [ 
                1.,      # n
                10.,       # D2D
                10.,    # D3D
                1.,     # F3D
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
model1["Definitions"] = m_gauss_3d_2d_t
model1["Verification"] = Checkme
model1["Supplements"] = MoreInfo

Modelarray = [model1]
