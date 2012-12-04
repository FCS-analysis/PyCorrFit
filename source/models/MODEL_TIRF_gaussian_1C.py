# -*- coding: utf-8 -*-
""" This file contains TIR one component models + Triplet
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
    """ 3D free diffusion measured with a gaussian lateral detection profile
        and an exponentially decaying profile in axial direction.

        x = sqrt(D*tau)*kappa
        taudiff = r_0²/(4*D)
        kappa = 1/d_eva
        w(i*x) = exp(x²)*erfc(x)
        gz = kappa² * 
             [ sqrt(D*tau/pi) - (2*D*tau*kappa² - 1)/(2*kappa) * w(i*x) ]
        g2D = 1 / [ pi*r_0² * (1.+tau/taudiff) ]
        G = 1/C_3D * g2D * gz


        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D: Diffusion coefficient
        [1] r_0: radius of the detection profile (FWHM)
        [2] d_eva: evanescent wave depth
        [2] C_3D : 3D Concentration
        *tau*: time differences from multiple tau correlator

        Returns: Normalized 3D correlation function for TIRF.
    """
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



def MoreInfo_6013(parms, countrate):
    """
        Supplementary variables:
        Beware that the effective volume is chosen arbitrarily.
         Effective detection volume:         
          V_eff  = np.pi * r_0**2 * d_eva
         Effective particle number:
          Neff = C_3D * Veff
    """
    D = parms[0]
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
m_3dtirsq6013 = [6013, "3D (Gauß/exp)","Simple 3D diffusion w/ TIR", CF_Gxyz_TIR_gauss]
labels_6013 = ["D [10 µm²/s]","r_0 [100 nm]", "d_eva [100 nm]", "C_3D [1000/µm³)"]
values_6013 = [0.0005420, 9.44, 1.0, .03011]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6013 = ["D [µm²/s]", "r_0 [nm]", "d_eva [nm]", "C_3D [1/µm³]"]
values_factor_human_readable_6013 = [10, 100, 100, 1000]
valuestofit_6013 = [True, False, False, True]
parms_6013 = [labels_6013, values_6013, valuestofit_6013,
              labels_human_readable_6013, values_factor_human_readable_6013]



# Pack the models
model1 = dict()
model1["Parameters"] = parms_6013
model1["Definitions"] = m_3dtirsq6013
model1["Supplements"] = MoreInfo_6013
model1["Verification"] = lambda parms: np.abs(parms)


Modelarray = [model1]
