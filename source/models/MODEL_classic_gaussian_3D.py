# -*- coding: utf-8 -*-
""" This file contains TIR one component models + Triplet
"""
import numpy as np                  # NumPy

# 3D simple gauss
def CF_Gxyz_gauss(parms, tau):
    # Model 6012
    """ 3D free diffusion with a Gaussian laser profile (eliptical).
        Single molecule fluorescence spectroscopy.

        G(tau) = offset + 1/( n*(1+tau/τ_diff) * sqrt(1 + tau/(SP²*τ_diff)) )


        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile:
        D = r0²/(4*τ_diff)
        Conc = n/( sqrt(pi³)*r0²*z0 )

            r0   lateral detection radius (waist of lateral gaussian)
            z0   axial detection length (waist of axial gaussian)
            D    Diffusion coefficient
            Conc Concentration of dye
            

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation volume.
        [1] τ_diff: characteristic residence time (diffusion).
        [2] SP: SP=z0/r0 describes the shape of the detection volume
        [3] offset
        *tau*: time differences from multiple tau correlator
    """
    n = parms[0]
    taudiff = parms[1]
    SP = parms[2]
    off = parms[3]

    BB = 1 / ( (1.+tau/taudiff) * np.sqrt(1.+tau/(SP**2*taudiff)) )
    G = off + 1/n * BB
    return G


# 3D blinking gauss
    # Model 6011
def CF_Gxyz_blink(parms, tau):
    """ 3D free diffusion and blinking effects.
        Single molecule fluorescence spectroscopy.
        Due to pH-reigned (de-)protonation (or other factors), blinking of 
        fluorescent molecules can be observed.
        (This is *CF_Gxyz_gauss* + blinking.
        See *CF_Gxyz_gauss* for more information)
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        G(tau) = offset + 1/( n*(1+tau/τ_diff) * sqrt(1 + tau/(SP²*τ_diff)) )
                    * ( 1+T/(1.-T)*exp(-tau/τ_trip) )

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation volume
        [1] T: coefficient describing fraction of non-fluorescent molecules
               0 <= T < 1
        [2] τ_diff: characteristic residence time in Triplett state
        [3] τ_trip: characteristic residence time (Diffusion)
        [4] SP: =z0/r0 describes the shape of the detection/excitation volume
        [5] offset
        *tau*: time differences from multiple tau correlator
    """
    n = parms[0]
    T = parms[1]
    tautrip = parms[2]
    taudiff = parms[3]
    SP = parms[4]
    off = parms[5]


    AA = 1. + T/(1.-T) * np.exp(-tau/tautrip)

    BB = 1 / ( (1.+tau/taudiff) * np.sqrt(1.+tau/(SP**2*taudiff)) )
    G = off + 1/n * AA * BB
    return G


def Check_6011(parms):
    parms[0] = np.abs(parms[0])
    T = parms[1]
    tautrip = np.abs(parms[2])
    parms[3] = taudiff = np.abs(parms[3])
    parms[4] = np.abs(parms[4])
    off = parms[5]
    
    # REMOVED (issue #2)
     ## Force triplet component to be smaller than diffusion
     #tautrip = min(tautrip, 0.9*taudiff)
     
    # Triplet fraction is between 0 and one.
    T = (0.<=T<1.)*T + .999999999*(T>=1)

    parms[1] = T
    parms[2] = tautrip

    return parms


# 3D + 3D + Triplet Gauß
    # Model 6030
def CF_Gxyz_gauss_3D3DT(parms, tau):
    """ Two component 3D free diffusion and a triplet component.
        Single molecule fluorescence spectroscopy, confocal setups, focused
        laser beam defines excitation volume.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *tautrip* to 0, if no triplet component is wanted.

        particle1 = F/( (1+tau/τ_1) * np.sqrt(1+tau/(τ_1*SP²)))
        particle2 = alpha²*(1-F)/( (1+tau/τ_2) * np.sqrt(1+tau/(τ_2*SP²)))
        triplet = 1 + T/(1-T)*np.exp(-tau/τ_trip)
        norm = (F + alpha*(1-F))²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation volume (n = n1+n2)
        [1] τ_1: diffusion time of particle species 1
        [2] τ_2: diffusion time of particle species 2
        [3] F: fraction of molecules of species 1 (n1 = n*F)
               0 <= F <= 1
        [4] SP: structural parameter z0/r0, describes the shape of the 
                detection/excitation volume
        [5] alpha: relative molecular brightness of particle
                   2 compared to particle 1 (alpha = q2/q1)
        [6] τ_trip: characteristic residence time in triplet state
        [7] T: coefficient describing fraction of non-fluorescent molecules
               0 <= T < 1
        [8] offset
        *tau*: time differences from multiple tau correlator
    """
    n=parms[0]
    taud1=parms[1]
    taud2=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip=parms[6]
    T=parms[7]
    off=parms[8]

    particle1 = F/( (1+tau/taud1) * np.sqrt(1+tau/(taud1*SP**2)))
    particle2 = alpha**2*(1-F)/( (1+tau/taud2) * np.sqrt(1+tau/(taud2*SP**2)))
    # If the fraction of dark molecules is zero, its ok. Python can also handle
    # exp(-1/inf).
    triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)
    # For alpha == 1, *norm* becomes one
    norm = (F + alpha*(1-F))**2

    G = 1/n*(particle1 + particle2)*triplet/norm + off
    return G

def Check_3D3DT(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = taud1 = np.abs(parms[1])
    parms[2] = taud2 = np.abs(parms[2])
    F=parms[3]
    parms[4]=np.abs(parms[4])
    parms[5]=np.abs(parms[5])
    tautrip=np.abs(parms[6])
    T=parms[7]
    off=parms[8]
    
    # REMOVED (issue #2)
     # Force triplet component to be smaller than diffusion times
     #tautrip = min(tautrip,taud1*0.9, taud2*0.9)
    
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[6] = tautrip
    parms[7] = T

    return parms


def MoreInfo_1C(parms, countrate):
    """ Return more information on the given model by using
        a given set of parameters.
    """
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


# 3D Model blink gauss
m_3dblink6011 = [6011, "3D+T (Gauß)","Simple 3D diffusion w/ triplet", 
                 CF_Gxyz_blink]
labels_6011 = ["n","T","τ_trip [ms]", "τ_diff [ms]", "SP", "offset"]
values_6011 = [4.0, 0.2, 0.07, 0.4, 5.0, 0.0]
valuestofit_6011 = [True, True, True, True, False, False]
parms_6011 = [labels_6011, values_6011, valuestofit_6011]

# 3D Model gauss
m_3dgauss6012 = [6012, "3D (Gauß)","Simple 3D diffusion", CF_Gxyz_gauss]
labels_6012 = ["n", "τ_diff [ms]", "SP", "offset"]
values_6012 = [4.0, 0.4, 5.0, 0.0]
valuestofit_6012 = [True, True, False, False]
parms_6012 = [labels_6012, values_6012, valuestofit_6012]

# 3D + 3D + T model gauss
m_gauss_3d_3d_t_mix_6030 = [6030, "3D+3D+T (Gauß)",
                            "Separate 3D diffusion + triplet, Gauß",
                            CF_Gxyz_gauss_3D3DT]
labels_6030  = ["n",
                "τ"+u"\u2081"+" [ms]",
                "τ"+u"\u2082"+" [ms]",
                "F"+u"\u2081", 
                "SP",
                u"\u03b1"+" (q"+u"\u2082"+"/q"+u"\u2081"+")", 
                "τ_trip [ms]",
                "T",
                "offset"
                ]
values_6030 = [ 
                25,      # n
                5,       # taud1
                1000,    # taud2
                0.75,     # F
                5,       # SP
                1.0,     # alpha
                0.001,       # tautrip
                0.01,       # T
                0.0      # offset
                ]        
valuestofit_6030 = [True, True, False, False, False, False, True, True, False]
parms_6030 = [labels_6030, values_6030, valuestofit_6030]


# Pack the models
model1 = dict()
model1["Parameters"] = parms_6011
model1["Definitions"] = m_3dblink6011
model1["Supplements"] = MoreInfo_1C
model1["Verification"] = Check_6011

model2 = dict()
model2["Parameters"] = parms_6012
model2["Definitions"] = m_3dgauss6012
model2["Supplements"] = MoreInfo_1C

model3 = dict()
model3["Parameters"] = parms_6030
model3["Definitions"] = m_gauss_3d_3d_t_mix_6030
model3["Verification"] = Check_3D3DT


Modelarray = [model1, model2, model3]