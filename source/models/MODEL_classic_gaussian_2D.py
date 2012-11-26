# -*- coding: utf-8 -*-
""" This file contains some simple 2D models for confocal microscopy
"""
import numpy as np                  # NumPy


# 2D simple gauss
def CF_Gxy_gauss(parms, tau):
    """ 2D free diffusion with a Gaussian laser profile.
        Single molecule fluorescence spectroscopy.

        G(tau) = offset + 1/( n * (1+tau/taudiff) )
    
        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r0 = 2*sigma):
        D = r0²/(4*taudiff)
        Conc = n/(pi*r0²)


        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation area.
        [1] taudiff: characteristic residence time (Diffusion).
        [3] offset
        *tau*: time differences from multiple tau correlator
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
    """ 2D free diffusion with a Gaussian laser profile.
        Single molecule fluorescence spectroscopy.

        triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)

        G(tau) = offset + 1/( n * (1+tau/taudiff) )*triplet
    
        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r0 = 2*sigma):
        D = r0²/(4*taudiff)
        Conc = n/(pi*r0²)

            

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation area.
        [1] taudiff: characteristic residence time (Diffusion).
        [2] tautrip: characteristic residence time in triplet state
        [3] T: coefficient describing fraction of non-fluorescent molecules
               0 <= T < 1
        [4] offset
        *tau*: time differences from multiple tau correlator
    """
    n = parms[0]
    taudiff = parms[1]
    tautrip = parms[2]
    T = parms[3]
    dc = parms[4]

    triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)

    BB = 1 / ( (1.+tau/taudiff) )
    G = dc + 1/n * BB * triplet
    return G



def Check_xy_T_gauss(parms):
    parms[0] = np.abs(parms[0])
    taudiff = parms[1] = np.abs(parms[1])
    tautrip = np.abs(parms[2])
    T=parms[3]
    
    # REMOVED (Issue #2)
     ## Force triplet component to be smaller than diffusion times
     #tautrip = min(tautrip,taudiff*0.9)
     
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)

    parms[2] = tautrip
    parms[3] = T
    return parms



# 2D + 2D + Triplet Gauß
    # Model 6031
def CF_Gxyz_gauss_2D2DT(parms, tau):
    """ Two component 2D free diffusion and a triplet component.
        Single molecule fluorescence spectroscopy, confocal setups, focused
        laser beam defines excitation volume.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *tautrip* to 0, if no triplet component is wanted.

        particle1 = F/( 1+tau/taud1 )
        particle2 = alpha²*(1-F)/( 1+tau/taud2 )
        triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)
        norm = (F + alpha*(1-F))²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation volume (n = n1+n2)
        [1] taud1: diffusion time of particle species 1
        [2] taud2: diffusion time of particle species 2
        [3] F: fraction of molecules of species 1 (n1 = n*F)
               0 <= F <= 1
        [4] alpha: relative molecular brightness of particle
                   2 compared to particle 1 (alpha = q2/q1)
        [5] tautrip: characteristic residence time in triplet state
        [6] T: coefficient describing fraction of non-fluorescent molecules
               0 <= T < 1
        [7] offset
        *tau*: time differences from multiple tau correlator
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
    parms[1] = taud1 = np.abs(parms[1])
    parms[2] = taud2 = np.abs(parms[2])
    F=parms[3]
    parms[4] = np.abs(parms[4])
    tautrip = np.abs(parms[5])
    T=parms[6]
    off=parms[7]
    
    ## REMOVED (Issue #2)
     ## Force triplet component to be smaller than diffusion times
     #tautrip = min(tautrip,taud1*0.9, taud2*0.9)
     
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[5] = tautrip
    parms[6] = T

    return parms


def MoreInfo_6001(parms, countrate):
    """ 
    """
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


# 2D Model Gauss
m_twodga6001 = [6001, "2D (Gauß)","2D confocal diffusion", CF_Gxy_gauss]
labels_6001 = ["n", "τ_diff [ms]", "offset"]
values_6001 = [4.0, 0.4, 0.0]
valuestofit_6001 = [True, True, False]
parms_6001 = [labels_6001, values_6001, valuestofit_6001]


# 2D Model Gauss with Triplet
m_twodga6002 = [6002, "2D+T (Gauß)","2D confocal diffusion with triplet", 
                CF_Gxy_T_gauss]
labels_6002 = ["n", "τ_diff [ms]",  "τ trip [ms]", "T", "offset"]
values_6002 = [4.0, 0.4, 0.001, 0.01, 0.0]
valuestofit_6002 = [True, True, True, True, False]
parms_6002 = [labels_6002, values_6002, valuestofit_6002]


# 2D + 2D + T model gauss
m_gauss_2d_2d_t_mix_6031 = [6031, "2D+2D+T (Gauß)",
                            "Separate 2D diffusion + triplet, Gauß",
                            CF_Gxyz_gauss_2D2DT]
labels_6031  = ["n",
                "τ"+u"\u2081"+" [ms]",
                "τ"+u"\u2082"+" [ms]",
                "F"+u"\u2081", 
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                "τ trip [ms]",
                "T",
                "offset"
                ]
values_6031 = [ 
                25,      # n
                5,       # taud1
                1000,    # taud2
                0.75,     # F
                1.0,     # alpha
                0.001,       # tautrip
                0.01,       # T
                0.0      # offset
                ]        
valuestofit_6031 = [True, True, False, False, False, True, True, False]
parms_6031 = [labels_6031, values_6031, valuestofit_6031]







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
model3["Supplements"] = MoreInfo_6001
model3["Verification"] = Check_6031


Modelarray = [model1, model2, model3]
