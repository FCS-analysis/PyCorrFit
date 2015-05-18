# -*- coding: utf-8 -*-
"""
This file contains 3D+3D TIR-FCS models.
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


# 3D + 3D no binding TIRF
def CF_Gxyz_TIR_square_3d3d(parms, tau, wixi=wixi):
    u""" Two-component three-dimensional free diffusion
        with a square-shaped lateral detection area taking into account
        the size of the point spread function; and an exponential
        decaying profile in axial direction.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D1  3D Diffusion coefficient (species 1)
        [1] D_3D2  3D Diffusion coefficient of bound species 2
        [2] σ      Lateral size of the point spread function
                   σ = σ₀ * λ / NA
        [3] a      Side size of the square-shaped detection area
        [4] d_eva  Evanescent penetration depth
        [5] C_3D1  Concentration of species 1
        [6] C_3D2  Concentration of species 2
        [7] α      Relative molecular brightness of particle
                   2 compared to particle 1 (α = q₂/q₁)
        *tau* - lag time
    """
    D_3D1 = parms[0]
    D_3D2 = parms[1]
    sigma = parms[2]
    a = parms[3]
    kappa = 1/parms[4]
    Conc_3D1 = parms[5]
    Conc_3D2 = parms[6]
    alpha = parms[7]

    ## First, the 3D diffusion of species 1
    # Axial correlation    
    x1 = np.sqrt(D_3D1*tau)*kappa
    w_ix1 = wixi(x1)
    gz1 = np.sqrt(D_3D1*tau/np.pi) - (2*D_3D1*tau*kappa**2 - 1)/(2*kappa) * \
          w_ix1
    # Lateral correlation
    gx1_1 = 2/(a**2*np.sqrt(np.pi)) * np.sqrt(sigma**2+D_3D1*tau) * \
            ( np.exp(-a**2/(4*(sigma**2+D_3D1*tau))) -1 )
    gx2_1 = 1/a * sps.erf( a / (2*np.sqrt(sigma**2 + D_3D1*tau))) 
    gx1 =  gx1_1 + gx2_1
    gxy1 = gx1**2
    # Non normalized correlation function
    g3D1 = Conc_3D1 * gxy1 * gz1

    ## Second, the 3D diffusion of species 2
    # Axial correlation    
    x2 = np.sqrt(D_3D2*tau)*kappa
    w_ix2 = wixi(x2)
    gz2 = np.sqrt(D_3D2*tau/np.pi) - (2*D_3D2*tau*kappa**2 - 1)/(2*kappa) * \
          w_ix2
    # Lateral correlation
    gx1_2 = 2/(a**2*np.sqrt(np.pi)) * np.sqrt(sigma**2+D_3D2*tau) * \
            ( np.exp(-a**2/(4*(sigma**2+D_3D2*tau))) -1 )
    gx2_2 = 1/a * sps.erf( a / (2*np.sqrt(sigma**2 + D_3D2*tau))) 
    gx2 =  gx1_2 + gx2_2
    gxy2 = gx2**2
    # Non normalized correlation function
    g3D2 = alpha**2 * Conc_3D2 * gxy2 * gz2

    ## Finally the Prefactor
    F = (Conc_3D1 + alpha * Conc_3D2) / kappa
    G = (g3D1 + g3D2) / F**2
    return G


# 3D-3D Model TIR
m_tir_3d_3d_mix_6023 = [6023, u"3D+3D",
                        "Separate 3D diffusion, 3D TIR",
                        CF_Gxyz_TIR_square_3d3d]
labels_6023 = [u"D"+u"\u2081"+u" [10 µm²/s]",
               u"D"+u"\u2082"+u" [10 µm²/s]",
               u"σ [100 nm]",
               u"a [100 nm]", 
               u"d_eva [100 nm]", 
               u"C"+u"\u2081"+u" [1000 /µm³]", 
               u"C"+u"\u2082"+u" [1000 /µm³]", 
               u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")"
                ]
values_6023 = [
                9.0,     # D_3D₁ [10 µm²/s]
                0.5,    # D_3D₂ [10 µm²/s]
                2.3,     # σ [100 nm]
                7.50,    # a [100 nm]
                1.0,     # d_eva [100 nm]
                0.01,    # conc.3D₁ [1000 /µm³]
                0.03,    # conc.3D₂ [1000 /µm³]
                1       # alpha
                ]        
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6023 = [
                u"D"+u"\u2081"+u" [µm²/s]",
                u"D"+u"\u2082"+u" [µm²/s]",
                u"σ [nm]",
                u"a [nm]", 
                u"d_eva [nm]", 
                u"C"+u"\u2081"+u" [1/µm³]", 
                u"C"+u"\u2082"+u" [1/µm³]", 
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")"
                ]
values_factor_human_readable_6023 = [10, # "D_3D₁ [µm²/s]",
                10,     # D_3D₂ [10 µm²/s]
                100,    # σ [100 nm]
                100,    # a [100 nm]
                100,    # d_eva [100 nm]
                1000,   # conc.3D₁ [1000 /µm³]
                1000,   # conc.3D₂ [1000 /µm³]
                1       # alpha
                ]
valuestofit_6023 = [False, True, False, False, False, False, True, False]
parms_6023 = [labels_6023, values_6023, valuestofit_6023, 
              labels_human_readable_6023, values_factor_human_readable_6023]


model1 = dict()
model1["Parameters"] = parms_6023
model1["Definitions"] = m_tir_3d_3d_mix_6023
model1["Verification"] = lambda parms: np.abs(parms)


Modelarray = [model1]
