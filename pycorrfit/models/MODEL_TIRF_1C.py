# -*- coding: utf-8 -*-
"""
This file contains TIR one component models
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

def CF_Gxy_TIR_square(parms, tau):
    # Model 6000
    u""" Two-dimensional diffusion with a square shaped lateral detection
        area taking into account the size of the point spread function.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D      Diffusion coefficient
        [1] σ      Lateral size of the point spread function
                   σ = σ₀ * λ / NA
        [2] a      Side size of the square-shaped detection area
        [3] C_2D   Particle concentration in detection area
        *tau* - lag time

        Please refer to the documentation of PyCorrFit
        for further information on this model function.
        
        Returns: Normalized Lateral correlation function w/square pinhole.
    """
    D = parms[0]
    sigma = parms[1]
    a = parms[2]
    Conc = parms[3]

    var1 = sigma**2+D*tau
    AA = 2*np.sqrt(var1)/(a**2*np.sqrt(np.pi))
    BB = np.exp(-a**2/(4*(var1))) - 1
    CC = sps.erf(a/(2*np.sqrt(var1)))/a
    # gx = AA*BB+CC
    # gxy = gx**2
    # g2D = gxy * eta**2 * Conc
    # F = 1/(eta*Conc)
    # G = g2D / F**2
    G = 1/Conc * (AA*BB+CC)**2
    return G


# 3D free tir
def CF_Gxyz_TIR_square(parms, tau, wixi=wixi):
    # Model 6010
    u""" Three-dimensional diffusion with a square-shaped lateral
        detection area taking into account the size of the
        point spread function; and an exponential decaying profile
        in axial direction.
        
        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D      Diffusion coefficient
        [1] σ      Lateral size of the point spread function
                   σ = σ₀ * λ / NA
        [2] a      Side size of the square-shaped detection area
        [3] d_eva  Evanescent penetration depth
        [4] C_3D   Particle concentration in detection volume
        *tau* - lag time

        Please refer to the documentation of PyCorrFit
        for further information on this model function.
        
        Returns: 3D correlation function for TIR-FCS w/square pinhole
    """
    D = parms[0]
    sigma = parms[1]
    a = parms[2]
    kappa = 1/parms[3]
    Conc = parms[4]
    ### Calculate gxy

    # Axial correlation    
    x = np.sqrt(D*tau)*kappa
    w_ix = wixi(x)
    gz = np.sqrt(D*tau/np.pi) - (2*D*tau*kappa**2 - 1)/(2*kappa) * w_ix

    # Lateral correlation
    gx1 = 2/(a**2*np.sqrt(np.pi)) * np.sqrt(sigma**2+D*tau) * \
          ( np.exp(-a**2/(4*(sigma**2+D*tau))) -1 )
    gx2 = 1/a * sps.erf( a / (2*np.sqrt(sigma**2 + D*tau))) 
    gx =  gx1 + gx2
    gxy = gx**2

    # Non normalized correlation function
    # We do not need eta after normalization
    # g = eta**2 * Conc * gxy * gz
    g = Conc * gxy * gz
    # Normalization:
    # F = eta * Conc / kappa
    F = Conc / kappa
    G = g / F**2
    return G


def MoreInfo_6000(parms, countrate=None):
    u"""Supplementary parameters:
        For a>>sigma, the correlation function at tau=0 corresponds to:
        [4] G(τ=0) = 1/(N_eff) * ( 1-2*σ/(sqrt(π)*a) )²
        Effective detection area:
        [5] A_eff [µm²] = a²
        Effective particle number in detection area:
        [6] N_eff = A_eff * C_2D
    """
    #D = parms[0]
    #sigma = parms[1]
    a = parms[2]
    Conc = parms[3]
    Info=list()

    # Detection area:
    Aeff = a**2 
    # Particel number
    Neff = Aeff * Conc
    # Correlation function at tau = 0
    G_0 = CF_Gxy_TIR_square(parms, 0)

    Info.append(["G(0)", G_0])

    # 10 000 nm² = 0.01 µm²
    # Aeff * 10 000 nm² * 10**(-6)µm²/nm² = Aeff * 0.01 * µm²
    # Have to divide Aeff by 100
    Info.append([u"A_eff [µm²]", Aeff / 100])
    Info.append(["N_eff", Neff])
    if countrate is not None:
        # CPP
        cpp = countrate/Neff
        Info.append(["cpp [kHz]", cpp])
    return Info


def MoreInfo_6010(parms, countrate):
    u"""Supplementary parameters:
        Molarity:
        [5] C_3D [nM] = C_3D [1000/µm³] * 10000/6.0221415
        Effective detection volume:
        [6] V_eff = a² * d_eva
        Effective particle number:
        [7] N_eff = V_eff * C_3D
        For a>>σ, the correlation function at τ=0 corresponds to:
        [8] G(τ=0) = 1/(2*N_eff) * ( 1-2*σ/(sqrt(π)*a) )²
    """
    # 3D Model TIR square
    # 3D TIR (□xσ/exp),Simple 3D diffusion w/ TIR, fct.CF_Gxyz_square_tir
    # D [10 µm²/s],σ [100 nm],a [100 nm],d_eva [100 nm],[conc.] [1000 /µm³]
    #sigma = parms[1]
    a = parms[2]
    d_eva = parms[3]
    conc = parms[4]
    # Sigma

    Info = list()
    # Molarity [nM]:
    # 1000/(µm³)*10**15µm³/l * mol /(6.022*10^23) * 10^9 n
    cmol = conc * 10000/6.0221415
    # Effective volume [al]:
    Veff = a**2 * d_eva
    # Effective particel number
    Neff = a**2 * d_eva * conc
    # Correlation function at tau = 0
    G_0 = CF_Gxyz_TIR_square(parms, 0)

    Info.append(["G(0)", G_0])

    Info.append(["C_3D [nM]", cmol])
    # atto liters
    # 1 000 000 nm³ = 1 al
    Info.append(["V_eff [al]", Veff])
    Info.append(["N_eff", Neff])
    if countrate is not None:
        # CPP
        cpp = countrate/Neff
        Info.append(["cpp [kHz]", cpp])
    return Info



# 2D Model Square
m_twodsq6000 = [6000, u"2D", u"2D diffusion w/ square pinhole",
                CF_Gxy_TIR_square]
labels_6000 = [u"D [10 µm²/s]",
               u"σ [100 nm]",
               u"a [100 nm]",
               u"C_2D [100 /µm²]"]
values_6000 = [0.054, 2.3, 7.5, .6] # [D,lamb,NA,a,conc]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6000 = [u"D [µm²/s]",
                              u"σ [nm]",
                              u"a [nm]",
                              u"C_2D [1/µm²]"]
values_factor_human_readable_6000 = [10, 100, 100, 100]
valuestofit_6000 = [True, False, False, True]      # Use as fit parameter?
parms_6000 = [labels_6000, values_6000, valuestofit_6000,
              labels_human_readable_6000, values_factor_human_readable_6000]

# 3D Model TIR square
m_3dtirsq6010 = [6010, u"3D", "Simple 3D diffusion w/ TIR",
                 CF_Gxyz_TIR_square]
labels_6010 = [u"D [10 µm²/s]",
               u"σ [100 nm]",
               u"a [100 nm]",
               u"d_eva [100 nm]",
               u"C_3D [1000 /µm³]"]
values_6010 = [0.520, 2.3, 7.5, 1.0, .0216]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6010 = [u"D [µm²/s]",
                              u"σ [nm]",
                              u"a [nm]",
                              u"d_eva [nm]",
                              u"C_3D [1/µm³]"]
values_factor_human_readable_6010 = [10, 100, 100, 100, 1000]
valuestofit_6010 = [True, False, False, False, True]
parms_6010 = [labels_6010, values_6010, valuestofit_6010,
              labels_human_readable_6010, values_factor_human_readable_6010]



# Pack the models
model1 = dict()
model1["Parameters"] = parms_6000
model1["Definitions"] = m_twodsq6000
model1["Supplements"] = MoreInfo_6000
model1["Verification"] = lambda parms: np.abs(parms)

model2 = dict()
model2["Parameters"] = parms_6010
model2["Definitions"] = m_3dtirsq6010
model2["Supplements"] = MoreInfo_6010
model2["Verification"] = lambda parms: np.abs(parms)


Modelarray = [model1, model2]
