# -*- coding: utf-8 -*-
"""
This file contains TIR one component models + Triplet
"""
import numpy as np                  # NumPy
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

def CF_Gxyz_TIR_gauss(parms, tau):
    u""" Three-dimensional free diffusion with a Gaussian lateral 
        detection profile and an exponentially decaying profile
        in axial direction.

        x = sqrt(D*τ)*κ
        κ = 1/d_eva
        w(i*x) = exp(x²)*erfc(x)
        gz = κ * [ sqrt(D*τ/π) + (1 - 2*D*τ*κ)/(2*κ) * w(i*x) ]
        g2D = 1 / [ π (r₀² + 4*D*τ) ]
        G = 1/C_3D * g2D * gz


        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D      Diffusion coefficient
        [1] r₀     Lateral extent of the detection volume
        [2] d_eva  Evanescent field depth
        [3] C_3D   Particle concentration in the confocal volume
        *tau* - lag time
    """
    # model 6013
    D = parms[0]
    r0 = parms[1]
    deva = parms[2]
    Conc = parms[3]

    # Calculate sigma: width of the gaussian approximation of the PSF
    Veff = np.pi * r0**2 * deva
    Neff = Conc * Veff

    taudiff = r0**2/(4*D)
    # 2D gauss component
    # G2D = 1/N2D * g2D = 1/(Aeff*Conc.2D) * g2D
    g2D = 1 / ( (1.+tau/taudiff) )

    # 1d TIR component
    # Axial correlation    
    kappa = 1/deva
    x = np.sqrt(D*tau)*kappa
    w_ix = wixi(x)

    # Gz = 1/N1D * gz = kappa / Conc.1D * gz
    gz = kappa * (np.sqrt(D*tau/np.pi) - (2*D*tau*kappa**2 - 1)/(2*kappa) * w_ix)

    # gz * g2D * 1/( deva *A2D) * 1 / Conc3D

    # Neff is not the actual particle number. This formula just looks nicer
    # this way.
    # What would be easier to get is:
    # 1 / (Conc * deva * np.pi * r0) * gz * g2D

    return 1 / (Neff) * g2D * gz
    


def CF_Gxyz_TIR_gauss_trip(parms, tau):
    u""" Three-dimensional free diffusion with a Gaussian lateral 
        detection profile and an exponentially decaying profile
        in axial direction, including a triplet component.

        x = sqrt(D*τ)*κ
        κ = 1/d_eva
        w(i*x) = exp(x²)*erfc(x)
        gz = κ * [ sqrt(D*τ/π) + (1 - 2*D*τ*κ)/(2*κ) * w(i*x) ]
        g2D = 1 / [ π (r₀² + 4*D*τ) ]
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        G = 1/C_3D * g2D * gz * triplet


        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D      Diffusion coefficient
        [1] r₀     Lateral extent of the detection volume
        [2] d_eva  Evanescent field depth
        [3] C_3D   Particle concentration in the confocal volume
        [4] τ_trip  Characteristic residence time in triplet state
        [5] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        *tau* - lag time
    """
    # model 6014
    D = parms[0]
    r0 = parms[1]
    deva = parms[2]
    Conc = parms[3]
    tautrip=parms[4]
    T=parms[5]

    # Calculate sigma: width of the gaussian approximation of the PSF
    Veff = np.pi * r0**2 * deva
    Neff = Conc * Veff

    taudiff = r0**2/(4*D)
    # 2D gauss component
    # G2D = 1/N2D * g2D = 1/(Aeff*Conc.2D) * g2D
    g2D = 1 / ( (1.+tau/taudiff) )

    # 1d TIR component
    # Axial correlation    
    kappa = 1/deva
    x = np.sqrt(D*tau)*kappa
    w_ix = wixi(x)

    # Gz = 1/N1D * gz = kappa / Conc.1D * gz
    gz = kappa * (np.sqrt(D*tau/np.pi) - (2*D*tau*kappa**2 - 1)/(2*kappa) * w_ix)

    ### triplet
    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)

    # Neff is not the actual particle number. This formula just looks nicer
    # this way.
    # What would be easier to get is:
    # 1 / (Conc * deva * np.pi * r0) * gz * g2D

    return 1 / (Neff) * g2D * gz * triplet



def MoreInfo_6013(parms, countrate=None):
    u"""Supplementary variables:
        Beware that the effective volume is chosen arbitrarily.
        Correlation function at lag time τ=0:
        [4] G(τ=0)
        Effective detection volume:         
        [5] V_eff  = π * r₀² * d_eva
        Effective particle concentration:
        [6] C_3D [nM] = C_3D [1000/µm³] * 10000/6.0221415
    """
    #D = parms[0]
    r0 = parms[1]
    deva = parms[2]
    Conc = parms[3]
    Info=list()
    # Detection area:
    Veff = np.pi * r0**2 * deva
    Neff = Conc * Veff
    # Correlation function at tau = 0
    G_0 = CF_Gxyz_TIR_gauss(parms, 0)
    Info.append(["G(0)", G_0])
    Info.append(["V_eff [al]", Veff])
    Info.append(["C_3D [nM]", Conc * 10000/6.0221415])
    if countrate is not None:
        # CPP
        cpp = countrate/Neff
        Info.append(["cpp [kHz]", cpp])
    return Info


def MoreInfo_6014(parms, countrate=None):
    u"""Supplementary variables:
        Beware that the effective volume is chosen arbitrarily.
        Correlation function at lag time τ=0:
        [6] G(τ=0)
        Effective detection volume:         
        [7] V_eff  = π * r₀² * d_eva
        Effective particle concentration:
        [8] C_3D [nM] = C_3D [1000/µm³] * 10000/6.0221415
    """
    #D = parms[0]
    r0 = parms[1]
    deva = parms[2]
    Conc = parms[3]
    Info=list()
    # Detection area:
    Veff = np.pi * r0**2 * deva
    Neff = Conc * Veff
    # Correlation function at tau = 0
    G_0 = CF_Gxyz_TIR_gauss(parms, 0)
    Info.append(["G(0)", G_0])
    Info.append(["V_eff [al]", Veff])
    Info.append(["C_3D [nM]", Conc * 10000/6.0221415])
    if countrate is not None:
        # CPP
        cpp = countrate/Neff
        Info.append(["cpp [kHz]", cpp])
    return Info


# 3D Model TIR gaussian
m_3dtirsq6013 = [6013, "3D","Simple 3D diffusion w/ TIR",
                 CF_Gxyz_TIR_gauss]
labels_6013 = [u"D [10 µm²/s]",
               u"r₀ [100 nm]",
               u"d_eva [100 nm]",
               u"C_3D [1000/µm³)"]
values_6013 = [2.5420,
               9.44,
               1.0,
               0.03011]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6013 = [u"D [µm²/s]",
                              u"r₀ [nm]",
                              u"d_eva [nm]",
                              u"C_3D [1/µm³]"]
values_factor_human_readable_6013 = [10, 
                                     100,
                                     100,
                                     1000]
valuestofit_6013 = [True, False, False, True]
parms_6013 = [labels_6013, values_6013, valuestofit_6013,
          labels_human_readable_6013, values_factor_human_readable_6013]

# Pack the models
model1 = dict()
model1["Parameters"] = parms_6013
model1["Definitions"] = m_3dtirsq6013
model1["Supplements"] = MoreInfo_6013
model1["Verification"] = lambda parms: np.abs(parms)


# 3D Model TIR gaussian + triplet
m_3dtirsq6014 = [6014, "T+3D","Simple 3D diffusion + triplet w/ TIR",
                 CF_Gxyz_TIR_gauss_trip]
labels_6014 = [u"D [10 µm²/s]",
               u"r₀ [100 nm]",
               u"d_eva [100 nm]",
               u"C_3D [1000/µm³)",
               u"τ_trip [ms]",
               u"T"]
values_6014 = [2.5420,
               9.44,
               1.0,
               0.03011,
               0.001,
               0.01]
labels_human_readable_6014 = [u"D [µm²/s]",
                              u"r₀ [nm]",
                              u"d_eva [nm]",
                              u"C_3D [1/µm³]",
                              u"τ_trip [µs]",
                              u"T"]
values_factor_human_readable_6014 = [10,
                                     100,
                                     100,
                                     1000,
                                     1000,
                                     1]
valuestofit_6014 = [True, False, False, True, False, False]
parms_6014 = [labels_6014, values_6014, valuestofit_6014,
          labels_human_readable_6014, values_factor_human_readable_6014]

# Pack the models
model2 = dict()
model2["Parameters"] = parms_6014
model2["Definitions"] = m_3dtirsq6014
model2["Supplements"] = MoreInfo_6014
model2["Verification"] = lambda parms: np.abs(parms)


Modelarray = [model1, model2]
