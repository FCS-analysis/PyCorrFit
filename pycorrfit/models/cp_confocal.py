"""Confocal fitting model components"""
import numpy as np


def threed(tau, taudiff, SP):
    return 1/((1 + tau/taudiff) * np.sqrt(1+tau/(taudiff*SP**2)))


def twod(tau, taudiff):
    return 1/((1 + tau/taudiff))