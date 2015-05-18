# -*- coding: utf-8 -*-
"""
This file contains 3D+2D TIR-FCS models.
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


# 3D + 2D no binding TIRF
def CF_Gxyz_TIR_square_3d2d(parms, tau, wixi=wixi):
    u""" Two-component two- and three-dimensional diffusion
        with a square-shaped lateral detection area taking into account
        the size of the point spread function; and an exponential
        decaying profile in axial direction.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D    Diffusion coefficient of freely diffusing species
        [1] D_2D    Diffusion coefficient of surface bound species
        [2] σ       Lateral size of the point spread function
                    σ = σ₀ * λ / NA
        [3] a       Side size of the square-shaped detection area
        [4] d_eva   Evanescent penetration depth
        [5] C_3D    Concentration of freely diffusing species
        [6] C_2D    Concentration of surface bound species
        [7] α       Relative molecular brightness of 3D particle
                    compared to 2D particle (α = q3D/q2D)
        *tau* - lag time
    """
    D_3D = parms[0]
    D_2D = parms[1]
    sigma = parms[2]
    a = parms[3]
    kappa = 1/parms[4]
    Conc_3D = parms[5]
    Conc_2D = parms[6]
    alpha = parms[7]

    ## First the 2D-diffusion at z=0
    var1 = sigma**2+D_2D*tau
    AA = 2*np.sqrt(var1)/(a**2*np.sqrt(np.pi))
    BB = np.exp(-a**2/(4*(var1))) - 1
    CC = sps.erf(a/(2*np.sqrt(var1)))/a
    # gx = AA*BB+CC
    # gxy = gx**2
    # g2D = Conc_2D * gxy
    g2D =  Conc_2D * (AA*BB+CC)**2

    ## Second the 3D diffusion for z>0
    # Axial correlation    
    x = np.sqrt(D_3D*tau)*kappa
    w_ix = wixi(x)
    gz = np.sqrt(D_3D*tau/np.pi) - (2*D_3D*tau*kappa**2 - 1)/(2*kappa) * w_ix
    # Lateral correlation
    gx1 = 2/(a**2*np.sqrt(np.pi)) * np.sqrt(sigma**2+D_3D*tau) * \
          ( np.exp(-a**2/(4*(sigma**2+D_3D*tau))) -1 )
    gx2 = 1/a * sps.erf( a / (2*np.sqrt(sigma**2 + D_3D*tau))) 
    gx =  gx1 + gx2
    gxy = gx**2
    # Non normalized correlation function
    g3D = alpha**2 * Conc_3D * gxy * gz

    ## Finally the Prefactor
    F = alpha * Conc_3D / kappa + Conc_2D
    G = (g3D + g2D) / F**2
    return G


# 3D-2D Model TIR
m_tir_3d_2d_mix_6020 = [6020, u"3D+2D",
                        "Separate 3D and 2D diffusion, 3D TIR",
                        CF_Gxyz_TIR_square_3d2d]
labels_6020 = [u"D_3D [10 µm²/s]",
               u"D_2D [10 µm²/s]",
               u"σ [100 nm]",
               u"a [100 nm]", 
               u"d_eva [100 nm]", 
               u"C_3D [1000 /µm³]", 
               u"C_2D [100 /µm²]", 
               u"\u03b1"+" (q3D/q2D)"
                ]
values_6020 = [
                50.0,     # D_3D [10 µm²/s]
                0.81,    # D_2D [10 µm²/s]
                2.3,     # σ [100 nm]
                7.50,    # a [100 nm]
                1.0,     # d_eva [100 nm]
                0.01,    # conc.3D [1000 /µm³]
                0.03,    # conc.2D [100 /µm²]
                1        # alpha
                ]        
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6020 = [
                u"D_3D [µm²/s]",
                u"D_2D [µm²/s]",
                u"σ [nm]",
                u"a [nm]", 
                u"d_eva [nm]", 
                u"C_3D [1/µm³]", 
                u"C_2D [1/µm²]", 
                u"\u03b1"+" (q3D/q2D)"
                ]
values_factor_human_readable_6020 = [
                10,     # D_3D [µm²/s]
                10,     # D_2D [10 µm²/s]
                100,    # σ [100 nm]
                100,    # a [100 nm]
                100,    # d_eva [100 nm]
                1000,   # conc.3D [1000 /µm³]
                100,    # conc.2D [100 /µm²]
                1       # alpha
                ]
valuestofit_6020 = [False, True, False, False, False, False, True, False]
parms_6020 = [labels_6020, values_6020, valuestofit_6020, 
              labels_human_readable_6020, values_factor_human_readable_6020]


model1 = dict()
model1["Parameters"] = parms_6020
model1["Definitions"] = m_tir_3d_2d_mix_6020
model1["Verification"] = lambda parms: np.abs(parms)

Modelarray = [model1]
