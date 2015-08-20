# -*- coding: utf-8 -*-
"""
    PyCorrFit
    This file contains a 3D+2D+T confocal FCS model.

    Copyright (C) 2011-2012  Paul Müller

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License 
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division

import numpy as np

# 3D + 2D + T
def CF_Gxyz_3d2dT_gauss(parms, tau):
    u""" Two-component, two- and three-dimensional diffusion
        with a Gaussian laser profile, including a triplet component.
        The triplet factor takes into account blinking according to triplet
        states of excited molecules.
        Set *T* or *τ_trip* to 0, if no triplet component is wanted.

        particle2D = (1-F)/ (1+τ/τ_2D) 
        particle3D = α*F/( (1+τ/τ_3D) * sqrt(1+τ/(τ_3D*SP²)))
        triplet = 1 + T/(1-T)*exp(-τ/τ_trip)
        norm = (1-F + α*F)²
        G = 1/n*(particle1 + particle2)*triplet/norm + offset

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal volume
                    (n = n2D+n3D)
        [1] τ_2D    Diffusion time of surface bound particls
        [2] τ_3D    Diffusion time of freely diffusing particles
        [3] F       Fraction of molecules of the freely diffusing species
                    (n3D = n*F), 0 <= F <= 1
        [4] SP      SP=z₀/r₀ Structural parameter,
                         describes elongation of the confocal volume
        [5] α       Relative molecular brightness of particle
                    3D compared to particle 2D (α = q3D/q2D)
        [6] τ_trip  Characteristic residence time in triplet state
        [7] T       Fraction of particles in triplet (non-fluorescent) state
                    0 <= T < 1
        [8] offset
        *tau* - lag time
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
    if tautrip == 0 or T == 0:
        triplet = 1
    else:
        triplet = 1 + T/(1-T) * np.exp(-tau/tautrip)
    norm = (1-F + alpha*F)**2
    G = 1/n*(particle2D + particle3D)*triplet/norm

    return G + off

def Checkme(parms):
    parms[0] = np.abs(parms[0])
    parms[1] = np.abs(parms[1]) #= taud2D
    parms[2] = np.abs(parms[2]) #= taud3D
    F=parms[3]
    parms[4]=np.abs(parms[4])
    parms[5]=np.abs(parms[5])
    tautrip=np.abs(parms[6])
    T=parms[7]
    #off=parms[8]
    # Triplet fraction is between 0 and one. T may not be one!
    T = (0.<=T<1.)*T + .99999999999999*(T>=1)
    # Fraction of molecules may also be one
    F = (0.<=F<=1.)*F + 1.*(F>1)

    parms[3] = F
    parms[6] = tautrip
    parms[7] = T

    return parms


def MoreInfo(parms, countrate=None):
    u"""Supplementary parameters:
        Effective number of freely diffusing particles in 3D solution:
        [9]  n3D = n*F
        Effective number particles diffusing on 2D surface:
        [10] n2D = n*(1-F)
    """
    # We can only give you the effective particle number
    n = parms[0]
    F3d = parms[3]
    Info = list()
    # The enumeration of these parameters is very important for
    # plotting the normalized curve. Countrate must come out last!
    Info.append([u"n3D", n*F3d])
    Info.append([u"n2D", n*(1.-F3d)])
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append([u"cpp [kHz]", cpp])
    return Info


# 3D + 3D + T model gauss
m_gauss_3d_2d_t = [6032, u"T+3D+2D",
                   u"Separate 3D and 2D diffusion + triplet, Gauß",
                   CF_Gxyz_3d2dT_gauss]
labels  = [ u"n",
            u"τ_2D [ms]",
            u"τ_3D [ms]",
            u"F_3D", 
            u"SP",
            u"\u03b1"+" (q_3D/q_2D)", 
            u"τ_trip [ms]",
            u"T",
            u"offset"
                ]
values = [ 
                25,      # n
                240,     # taud2D
                0.1,     # taud3D
                0.5,     # F3D
                7,       # SP
                1.0,     # alpha
                0.001,   # tautrip
                0.01,    # T
                0.0      # offset
                ]
# For user comfort we add values that are human readable.
# Theese will be used for output that only humans can read.
labels_human_readable  = [  u"n",
                            u"τ_2D [ms]",
                            u"τ_3D [ms]",
                            u"F_3D", 
                            u"SP",
                            u"\u03b1"+" (q_3D/q_2D)", 
                            u"τ_trip [µs]",
                            u"T",
                            u"offset"
                            ]
values_factor_human_readable = [
                          1.,     # "n",
                          1.,     # "τ_2D [ms]",
                          1.,     # "τ_3D [ms]",
                          1.,     # "F_3D", 
                          1.,     # "SP",
                          1.,     # u"\u03b1"+" (q_3D/q_2D)", 
                          1000.,  # "τ_trip [µs]",
                          1.,     # "T",
                          1.      # "offset"
                ]
valuestofit = [True, True, True, True, False, False, False, False, False]
parms = [labels, values, valuestofit,
         labels_human_readable, values_factor_human_readable]


model1 = dict()
model1["Parameters"] = parms
model1["Definitions"] = m_gauss_3d_2d_t
model1["Verification"] = Checkme
model1["Supplements"] = MoreInfo

Modelarray = [model1]
