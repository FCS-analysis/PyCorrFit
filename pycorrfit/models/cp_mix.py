# -*- coding: utf-8 -*-
"""
Mixed components for fitting models.
"""

from __future__ import division
import numpy as np

def double_pnum(n,
                F1,
                alpha,
                comp1,
                kwargs1,
                comp2,
                kwargs2,
                ):
    u"""
    Double component models where the particle number is given in
    the model i.e. for confocal diffusion models.
    
    Parameters
    ----------
    n : float
        Total particle number
    F1 : float
        Fraction of particle species 1
    alpha : float
        Relative molecular brightness of particle
        2 compared to particle 1 (α = q₂/q₁)
    comp1, comp2 : callables
        The model functions for each of the components.
    kwargs1, kwargs2 : dicts
        The keyword arguments for `comp1` and `comp2`
    """
    norm = (F1 + alpha*(1-F1))**2

    g1 = F1 * comp1(**kwargs1)
    g2 = alpha**2 * (1-F1) * comp2(**kwargs2)
    
    G = 1/n * (g1 + g2) / norm
    
    return G