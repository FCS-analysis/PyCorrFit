"""Triplet components"""
import numpy as np


def trip(tau, tautrip, T):
    if tautrip == 0 or T == 0:
        AA = 1
    else:
        AA = 1 + T/(1-T) * np.exp(-tau / tautrip)

    return AA
