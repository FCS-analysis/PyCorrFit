# -*- coding: utf-8 -*-
"""  This file contains a 3D+2D+T confocal FCS model.
"""
import numpy as np                  # NumPy

# 3D + 2D + T
def CF_Gxyz_3d2dT_gauss(parms, tau):
    """ Two component 3D and 2D free diffusion and a triplet component.
        Single molecule fluorescence spectroscopy, confocal setups, focused
        laser beam defines excitation volume.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *tautrip* to 0, if no triplet component is wanted.
        *tautrip* is always smaller than 0.9*taud3D* or 0.9*taud2D*

        particle2D = (1-F)/ (1+tau/taud2D) 
        particle3D = alpha²*F/( (1+tau/taud3D) * sqrt(1+tau/(taud3D*SP²)))
        triplet = 1 + T/(1-T)*exp(-tau/tautrip)
        norm = (1-F + alpha*F)²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n: expected number of particles in observation volume (n = n2D+n3D)
        [1] taud2D: diffusion time of surface bound particle species
        [2] taud3D: diffusion time of 3D diffusing particle species
        [3] F: fraction of molecules of 3D diffusing species 1 (n3D = n*F)
               0 <= F <= 1
        [4] SP: structural parameter z0/r0, describes the shape of the 
                detection/excitation volume
        [5] alpha: relative molecular brightness of particle
                   3D compared to particle 2D (alpha = q3D/q2D)
        [6] tautrip: characteristic residence time in triplet state
        [7] T: coefficient describing fraction of non-fluorescent molecules
               0 <= T < 1
        [8] offset
        *tau*: time differences from multiple tau correlator
    """
    n=parms[0]
    taud2D=parms[1]
    taud3D=parms[2]
    F=parms[3]
    SP=parms[4]
    alpha=parms[5]
    tautrip=parms[6]
    T=parms[7]
    off=parms[8]


    particle2D = (1-F)/ (1+tau/taud2D) 
    particle3D = alpha**2*F/( (1+tau/taud3D) * np.sqrt(1+tau/(taud3D*SP**2)))
    triplet = 1 + T/(1-T)*np.exp(-tau/tautrip)
    norm = (1-F + alpha*F)**2
    G = 1/n*(particle2D + particle3D)*triplet/norm

    return G + off

def Checkme(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = taud2D = np.abs(parms[1])
    parms[2] = taud3D = np.abs(parms[2])
    F=parms[3]
    parms[4]=np.abs(parms[4])
    parms[5]=np.abs(parms[5])
    tautrip=np.abs(parms[6])
    T=parms[7]
    off=parms[8]
    
    # REMOVED (issue #2)
     ## Force triplet component to be smaller than diffusion times
     #tautrip = min(tautrip,taud2D*0.9, taud3D*0.9)
     
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[6] = tautrip
    parms[7] = T

    return parms


def MoreInfo(parms, countrate):
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


# 3D + 3D + T model gauss
m_gauss_3d_2d_t = [6032, "3D+2D+T (Gauß)",
                            "Separate 3D and 2D diffusion + triplet, Gauß",
                            CF_Gxyz_3d2dT_gauss]
labels  = ["n",
                "τ_2D [ms]",
                "τ_3D [ms]",
                "F_3D", 
                "SP",
                u"\u03b1"+" (q_3D/q_2D)", 
                "τ_trip [ms]",
                "T",
                "offset"
                ]
values = [ 
                25,      # n
                100,       # taud2D
                0.1,    # taud3D
                0.45,     # F3D
                7,       # SP
                1.0,     # alpha
                0.001,       # tautrip
                0.01,       # T
                0.0      # offset
                ]        
valuestofit = [True, True, True, True, False, False, False, False, False]
parms = [labels, values, valuestofit]


model1 = dict()
model1["Parameters"] = parms
model1["Definitions"] = m_gauss_3d_2d_t
model1["Verification"] = Checkme
model1["Supplements"] = MoreInfo

Modelarray = [model1]
