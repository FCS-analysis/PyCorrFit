# -*- coding: utf-8 -*-
""" This file contains 2D+2D TIR-FCS models.
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


# 2D + 2D no binding TIRF
def CF_Gxy_TIR_square_2d2d(parms, tau, wixi=wixi):
    """ 2D diffusion measured with a square pinhole in a TIR-FCS setup and
        considering two species:
        - Surface bound species 1
        - Surface bound species 2
        without binding/unbinding.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_2D1: 2D Diffusion coefficient (species 1)
        [1] D_2D2: 2D Diffusion coefficient of bound species 2
        [2] sigma: lateral size of the point spread function
                   sigma = simga_0 * lambda / NA
        [3] a: side size of the square pinhole
        [4] d_eva: evanescent decay length (decay to 1/e)
        [5] C_2D1: 2-dimensional concentration of species 1
        [6] C_2D2: 2-dimensional concentration of species 2
        [7] alpha: relative molecular brightness of particle
                   2 compared to 1 (alpha = q2/q1)
        *tau*: time differences from multiple tau correlator

        Returns: 2D correlation function for TIR-FCS w/square pinhole and
                 2D diffusion with two components.
    """
    D_2D1 = parms[0]
    D_2D2 = parms[1]
    sigma = parms[2]
    a = parms[3]
    kappa = 1/parms[4]
    Conc_2D1 = parms[5]
    Conc_2D2 = parms[6]
    alpha = parms[7]

    ## First the 2D-diffusion of species 1
    var1 = sigma**2+D_2D1*tau
    AA1 = 2*np.sqrt(var1)/(a**2*np.sqrt(np.pi))
    BB1 = np.exp(-a**2/(4*(var1))) - 1
    CC1 = sps.erf(a/(2*np.sqrt(var1)))/a
    # gx = AA*BB+CC
    # gxy = gx**2
    # g2D = Conc_2D * gxy
    g2D1 =  Conc_2D1 * (AA1*BB1+CC1)**2

    ## Second the 2D-diffusion of species 2
    var2 = sigma**2+D_2D2*tau
    AA2 = 2*np.sqrt(var2)/(a**2*np.sqrt(np.pi))
    BB2 = np.exp(-a**2/(4*(var2))) - 1
    CC2 = sps.erf(a/(2*np.sqrt(var2)))/a
    # gx = AA*BB+CC
    # gxy = gx**2
    # g2D = Conc_2D * gxy
    g2D2 =  alpha**2 * Conc_2D2 * (AA2*BB2+CC2)**2

    ## Finally the Prefactor
    F = Conc_2D1 + alpha * Conc_2D2
    G = (g2D1 + g2D2) / F**2
    return G


# 2D-2D Model TIR
m_tir_2d_2d_mix_6022 = [6022, u"2D+2D (□xσ)","Separate 2D diffusion, TIR", 
                        CF_Gxy_TIR_square_2d2d]
labels_6022 = [ "D"+u"\u2081"+u" [10 µm²/s]",
                "D"+u"\u2082"+u" [10 µm²/s]",
                u"σ [100 nm]",
                "a [100 nm]", 
                "d_eva [100 nm]", 
                "C"+u"\u2081"+u" [100 /µm²]", 
                "C"+u"\u2082"+u" [100 /µm²]", 
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")"
                ]
values_6022 = [
                0.90,     # D_2D₁ [10 µm²/s]
                0.01,    # D_2D₂ [10 µm²/s]
                2.3,     # σ [100 nm]
                7.50,    # a [100 nm]
                1.0,     # d_eva [100 nm]
                0.01,    # conc.2D₁ [100 /µm²]
                0.03,    # conc.2D₂ [100 /µm²]
                1        # alpha
                ]        
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6022 = [
                "D"+u"\u2081"+u" [µm²/s]",
                "D"+u"\u2082"+u" [µm²/s]",
                u"σ [nm]",
                "a [nm]", 
                "d_eva [nm]", 
                "C"+u"\u2081"+u" [1/µm²]", 
                "C"+u"\u2082"+u" [1/µm²]", 
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")"
                ]
values_factor_human_readable_6022 = [
                10, # D_2D₁ [10 µm²/s],
                10,     # D_2D₂ [10 µm²/s]
                100,    # σ [100 nm]
                100,    # a [100 nm]
                100,    # d_eva [100 nm]
                100,    # conc.2D₁ [100 /µm²]
                100,    # conc.2D₂ [100 /µm²]
                1
                ]
valuestofit_6022 = [False, True, False, False, False, False, True, False]
parms_6022 = [labels_6022, values_6022, valuestofit_6022, 
              labels_human_readable_6022, values_factor_human_readable_6022]


model1 = dict()
model1["Parameters"] = parms_6022
model1["Definitions"] = m_tir_2d_2d_mix_6022
model1["Verification"] = lambda parms: np.abs(parms)

Modelarray = [model1]
