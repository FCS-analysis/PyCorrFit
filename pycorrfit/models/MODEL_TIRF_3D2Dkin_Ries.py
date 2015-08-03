# -*- coding: utf-8 -*-
""" 
This file contains a TIR-FCS kineteics model function according to:
"Total Internal Reflection Fluorescence Correlation Spectroscopy: Effects
of Lateral Diffusion and Surface-Generated Fluorescence"
Jonas Ries, Eugene P. Petrov, and Petra Schwille
Biophysical Journal, Volume 95, July 2008, 390–399
"""
import numpy as np                  # NumPy
import scipy.special as sps
import numpy.lib.scimath as nps

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


# Lateral correlation function
def CF_gxy_square(parms, tau):
    u""" 2D free diffusion measured with a square pinhole.
        For the square pinhole, the correlation function can readily be
        calculated for a TIR-FCS setup.
        This function is called by other functions within this module.
        Attention:
        This is NOT g2D (or gCC), the non normalized correlation function.
        g2D = gxy * eta**2 * Conc,
        where eta is the molecular brightness, Conc the concentration and
        gxy is this function.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D      Diffusion coefficient
        [1] sigma  lateral size of the point spread function
                   sigma = simga_0 * lambda / NA
        [2] a      side size of the square pinhole
        *tau* - lag time

        Returns: Nonnormalized Lateral correlation function w/square pinhole.
    """
    D = parms[0]
    sigma = parms[1]
    a = parms[2]

    var1 = sigma**2+D*tau
    AA = 2*np.sqrt(var1)/(a**2*np.sqrt(np.pi))
    BB = np.exp(-a**2/(4*(var1))) - 1
    CC = sps.erf(a/(2*np.sqrt(var1)))/a
    # gx = AA*BB+CC
    # gxy = gx**2
    return (AA*BB+CC)**2


def CF_gz_CC(parms, tau, wixi=wixi):
    u""" Axial (1D) diffusion in a TIR-FCS setup.
        From Two species (bound/unbound) this is the bound part.
        This function is called by other functions within this module.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D     3D Diffusion coefficient (species A)
        [1] D_2D     2D Diffusion coefficient of bound species C
        [2] sigma    lateral size of the point spread function
                     sigma = simga_0 * lambda / NA
        [3] a        side size of the square pinhole
        [4] d_eva    evanescent decay length (decay to 1/e)
        [5] Conc_3D  3-dimensional concentration of species A
        [6] Conc_2D  2-dimensional concentration of species C
        [7] eta_3D   molecular brightness of species A
        [8] eta_2D   molecular brightness of species C
        [9] k_a      Surface association rate constant
        [10] k_d     Surface dissociation rate constant
        *tau* - lag time
    """
    D = parms[0]
    #D_2D = parms[1]
    #sigma = parms[2]
    # a = parms[3]
    #d_eva = parms[4]
    Conc_3D = parms[5]      # ligand concentration in solution
    Conc_2D = parms[6]
    eta_3D = parms[7]
    eta_2D = parms[8]
    k_a = parms[9]
    k_d = parms[10]
    # Define some other constants:
    K = k_a/k_d              # equilibrium constant
    Beta = 1/(1 + K*Conc_3D) # This is wrong in the Ries paper
    #Re = D / d_eva**2
    Rt = D * (Conc_3D / (Beta * Conc_2D))**2
    Rr = k_a * Conc_3D + k_d
    # Define even more constants:
    sqrtR1 = -Rr/(2*nps.sqrt(Rt)) + nps.sqrt( Rr**2/(4*Rt) - Rr )
    sqrtR2 = -Rr/(2*nps.sqrt(Rt)) - nps.sqrt( Rr**2/(4*Rt) - Rr )
    R1 = sqrtR1 **2
    R2 = sqrtR2 **2
    # Calculate return function
    A1 = eta_2D * Conc_2D / (eta_3D * Conc_3D) * Beta
    A2 = sqrtR1 * wixi(-nps.sqrt(tau*R2)) - sqrtR2 * wixi(-nps.sqrt(tau*R1))
    A3 = sqrtR1 - sqrtR2
    Sol = A1 * A2 / A3
    # There are some below numerical errors-imaginary numbers.
    # We do not want them.
    return np.real_if_close(Sol)


def CF_gz_AC(parms, tau, wixi=wixi):
    u""" Axial (1D) diffusion in a TIR-FCS setup.
        From Two species (bound/unbound) this is the cross correlation part.
        This function is called by other functions within this module.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D     3D Diffusion coefficient (species A)
        [1] D_2D     2D Diffusion coefficient of bound species C
        [2] sigma    lateral size of the point spread function
                     sigma = simga_0 * lambda / NA
        [3] a        side size of the square pinhole
        [4] d_eva    evanescent decay length (decay to 1/e)
        [5] Conc_3D  3-dimensional concentration of species A
        [6] Conc_2D  2-dimensional concentration of species C
        [7] eta_3D   molecular brightness of species A
        [8] eta_2D   molecular brightness of species C
        [9] k_a      Surface association rate constant
        [10] k_d     Surface dissociation rate constant
        *tau* - lag time
    """
    D = parms[0]
    #D_2D = parms[1]
    #sigma = parms[2]
    # a = parms[3]
    d_eva = parms[4]
    Conc_3D = parms[5]      # ligand concentration in solution
    Conc_2D = parms[6]
    eta_3D = parms[7]
    eta_2D = parms[8]
    k_a = parms[9]
    k_d = parms[10]
    # Define some other constants:
    K = k_a/k_d             # equilibrium constant
    Beta = 1/(1 + K*Conc_3D)
    Re = D / d_eva**2
    Rt = D * (Conc_3D / (Beta * Conc_2D))**2
    Rr = k_a * Conc_3D + k_d
    # Define even more constants:
    sqrtR1 = -Rr/(2*nps.sqrt(Rt)) + nps.sqrt( Rr**2/(4*Rt) - Rr )
    sqrtR2 = -Rr/(2*nps.sqrt(Rt)) - nps.sqrt( Rr**2/(4*Rt) - Rr )
    R1 = sqrtR1 **2
    R2 = sqrtR2 **2
    # And even more more:
    sqrtR3 = sqrtR1 + nps.sqrt(Re)
    sqrtR4 = sqrtR2 + nps.sqrt(Re)
    #R3 = sqrtR3 **2
    #R4 = sqrtR4 **2
    # Calculate return function
    A1 = eta_2D * Conc_2D * k_d / (eta_3D * Conc_3D)
    A2 = sqrtR4*wixi(-nps.sqrt(tau*R1)) - sqrtR3*wixi(-nps.sqrt(tau*R2))
    A3 = ( sqrtR1 - sqrtR2 ) * wixi( nps.sqrt(tau*Re) )
    A4 = ( sqrtR1 - sqrtR2 ) * sqrtR3 * sqrtR4
    Solution = A1 * ( A2 + A3 ) / A4
    # There are some below numerical errors-imaginary numbers.
    # We do not want them.
    return np.real_if_close(Solution)


def CF_gz_AA(parms, tau, wixi=wixi):
    u""" Axial (1D) diffusion in a TIR-FCS setup.
        From Two species (bound/unbound) this is the unbound part.
        This function is called by other functions within this module.

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D     3D Diffusion coefficient (species A)
        [1] D_2D     2D Diffusion coefficient of bound species C
        [2] sigma    lateral size of the point spread function
                     sigma = simga_0 * lambda / NA
        [3] a        side size of the square pinhole
        [4] d_eva    evanescent decay length (decay to 1/e)
        [5] Conc_3D  3-dimensional concentration of species A
        [6] Conc_2D  2-dimensional concentration of species C
        [7] eta_3D   molecular brightness of species A
        [8] eta_2D   molecular brightness of species C
        [9] k_a      Surface association rate constant
        [10] k_d     Surface dissociation rate constant
        *tau* - lag time
    """
    D = parms[0]
    #D_2D = parms[1]
    #sigma = parms[2]
    # a = parms[3]
    d_eva = parms[4]
    Conc_3D = parms[5]      # ligand concentration in solution
    Conc_2D = parms[6]
    eta_3D = parms[7]
    eta_2D = parms[8]
    k_a = parms[9]
    k_d = parms[10]
    # Define some other constants:
    d = d_eva
    K = k_a/k_d             # equilibrium constant
    Beta = 1/(1 + K*Conc_3D)
    Re = D / d_eva**2
    Rt = D * (Conc_3D / (Beta * Conc_2D))**2
    Rr = k_a * Conc_3D + k_d
    # Define even more constants:
    sqrtR1 = -Rr/(2*nps.sqrt(Rt)) + nps.sqrt( Rr**2/(4*Rt) - Rr )
    sqrtR2 = -Rr/(2*nps.sqrt(Rt)) - nps.sqrt( Rr**2/(4*Rt) - Rr )
    R1 = sqrtR1 **2
    R2 = sqrtR2 **2
    # And even more more:
    sqrtR3 = sqrtR1 + nps.sqrt(Re)
    sqrtR4 = sqrtR2 + nps.sqrt(Re)
    R3 = sqrtR3 **2
    R4 = sqrtR4 **2
    # Calculate return function
    Sum1 = d * nps.sqrt( Re*tau/np.pi )
    Sum2 = -d/2*(2*tau*Re -1) * wixi(np.sqrt(tau*Re))
    Sum3Mult1 = - eta_2D * Conc_2D * k_d / ( eta_3D * Conc_3D * 
                                            (sqrtR1 - sqrtR2) )
    S3M2S1M1 = sqrtR1/R3
    S3M2S1M2S1 = wixi(-nps.sqrt(tau*R1)) + -2*nps.sqrt(tau*R3/np.pi)
    S3M2S1M2S2 = ( 2*tau*sqrtR1*nps.sqrt(Re) + 2*tau*Re -1 ) * \
                 wixi(nps.sqrt(tau*Re))
    S3M2S2M1 = -sqrtR2/R4
    S3M2S2M2S1 = wixi(-nps.sqrt(tau*R2)) + -2*nps.sqrt(tau*R4/np.pi)
    S3M2S2M2S2 = ( 2*tau*sqrtR2*nps.sqrt(Re) + 2*tau*Re -1 ) * \
                 wixi(nps.sqrt(tau*Re))
    Sum3 = Sum3Mult1 * ( S3M2S1M1 * (S3M2S1M2S1 + S3M2S1M2S2) + 
                         S3M2S2M1 * (S3M2S2M2S1 + S3M2S2M2S2) )
    Sum = Sum1 + Sum2 + Sum3
    # There are some below numerical errors-imaginary numbers.
    # We do not want them.
    return np.real_if_close(Sum)


# 3D-2D binding/unbinding TIRF
def CF_Gxyz_TIR_square_ubibi(parms, tau, 
                         gAAz=CF_gz_AA, gACz=CF_gz_AC, gCCz=CF_gz_CC,
                         gxy=CF_gxy_square):
    u""" Two-component two- and three-dimensional diffusion
        with a square-shaped lateral detection area taking into account
        the size of the point spread function; and an exponential
        decaying profile in axial direction. This model covers binding
        and unbinding kintetics. 

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] D_3D    Diffusion coefficient of freely diffusing species A
        [1] D_2D    Diffusion coefficient of bound species C
        [2] σ       Lateral size of the point spread function
                    σ = σ₀ * λ / NA
        [3] a       Side size of the square-shaped detection area 
        [4] d_eva   Evanescent decay constant
        [5] C_3D    Concentration of species A in observation volume
        [6] C_2D    Concentration of species C in observation area
        [7] η_3D    Molecular brightness of species A
        [8] η_2D    Molecular brightness of species C
        [9] k_a     Surface association rate constant
        [10] k_d    Surface dissociation rate constant
        *tau* - lag time

        Returns: 3D correlation function for TIR-FCS w/square pinhole and
                 surface binding/unbinding.

        Model introduced in:
         Jonas Ries, Eugene P. Petrov, and Petra Schwille
         Total Internal Reflection Fluorescence Correlation Spectroscopy: 
         Effects of Lateral Diffusion and Surface-Generated Fluorescence
         Biophysical Journal, Vol.95, July 2008, 390–399
    """
    D_3D = parms[0]
    D_2D = parms[1]
    sigma = parms[2]
    a = parms[3]
    kappa = 1/parms[4]
    Conc_3D = parms[5]
    Conc_2D = parms[6]
    eta_3D = parms[7]
    eta_2D = parms[8]
    #k_a = parms[9]
    #k_d = parms[10]
    ## We now need to copmute a real beast:
    # Inter species non-normalized correlation functions
    # gAA = gAAz * gxy(D_3D)
    # gAC = gACz * np.sqrt ( gxy(D_3D) * gxy(D_2D) )
    # gCC = gCCz * gxy(D_2D)
    # Nonnormalized correlation function
    # g = eta_3D * Conc_3D * ( gAA + 2*gAC + gCC )
    # Expectation value of fluorescence signal
    # F = eta_3D * Conc_3D / kappa + eta_2D * Conc_2D
    # Normalized correlation function
    # G = g / F**2
    ##
    # Inter species non-normalized correlation functions
    # The gijz functions take the same parameters as this function
    # The gxy function needs two different sets of parameters, depending
    # on the diffusion constant used.
    #    [0] D: Diffusion coefficient
    #    [1] sigma: lateral size of the point spread function
    #    [3] a: side size of the square pinhole
    parms_xy_2D = [D_2D, sigma, a]
    parms_xy_3D = [D_3D, sigma, a]
    # Here we go.
    gAA = gAAz(parms, tau) * gxy(parms_xy_3D, tau)
    gAC = gACz(parms, tau) * nps.sqrt( gxy(parms_xy_3D, tau) *
                                       gxy(parms_xy_2D, tau) )
    gCC = gCCz(parms, tau) * gxy(parms_xy_2D, tau)
    # Nonnormalized correlation function
    g = eta_3D * Conc_3D * ( gAA + 2*gAC + gCC )
    # Expectation value of fluorescence signal
    F = eta_3D * Conc_3D / kappa + eta_2D * Conc_2D
    # Normalized correlation function
    G = g / F**2
    # There are some below numerical errors-imaginary numbers.
    # We do not want them.
    return G.real
    #FNEW = eta_3D * Conc_3D / kappa
    #GNEW = eta_3D * Conc_3D * gCCz(parms, tau) / FNEW**2
    #return GNEW.real





# 3D-2D binding Model TIR
m_tir_3d_2d_ubib6021 = [6021, u"3D+2D+kin",
                        "Surface binding and unbinding, 3D TIR",
                        CF_Gxyz_TIR_square_ubibi]
labels_6021 = [u"D_3D [10 µm²/s]",
               u"D_2D [10 µm²/s]",
               u"σ [100 nm]",
               u"a [100 nm]", 
               u"d_eva [100 nm]", 
               u"C_3D [1000 /µm³]", 
               u"C_2D[100 /µm²]", 
               u"η_3D", 
               u"η_2D", 
               u"k_a [µm³/s]", 
               u"k_d [10³ /s]"
                ]
values_6021 = [
                9.0,      # D_3D [10 µm²/s]
                0.0,      # D_2D [10 µm²/s]
                2.3,      # σ [100 nm]
                7.50,     # a [100 nm]
                1.0,      # d_eva [100 nm]
                0.01,     # conc.3D [1000 /µm³]
                0.03,     # conc.2D [100 /µm²]
                1,        # η_3D
                1,        # η_2D
                0.00001,  # k_a [µm³/s]
                0.000064  # k_d [10³ /s]
                ]        
valuestofit_6021 = [False, True, False, False, False, False, True, False,
                    False, False, False]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable_6021 = [
                u"D_3D [µm²/s]",
                u"D_2D [µm²/s]",
                u"σ [nm]",
                u"a [nm]", 
                u"d_eva [nm]", 
                u"C_3D [1/µm³]", 
                u"C_2D [1/µm²]", 
                u"η_3D", 
                u"η_2D", 
                u"k_a [µm³/s]", 
                u"k_d [1/s]"
                ]
values_factor_human_readable_6021 = [10, # "D_3D [µm²/s]",
                10,     # D_2D [10 µm²/s]
                100,    # σ [100 nm]
                100,    # a [100 nm]
                100,    # d_eva [100 nm]
                1000,   # conc.3D [1000 /µm³]
                100,    # conc.2D [100 /µm²]
                1,      # η_3D
                1,      # η_2D
                1,      # k_a [µm³/s]
                1000   # k_d [10³ /s]
                ]
parms_6021 = [labels_6021, values_6021, valuestofit_6021,
              labels_human_readable_6021, values_factor_human_readable_6021]


model1 = dict()
model1["Parameters"] = parms_6021
model1["Definitions"] = m_tir_3d_2d_ubib6021
model1["Verification"] = lambda parms: np.abs(parms)


Modelarray = [model1]
