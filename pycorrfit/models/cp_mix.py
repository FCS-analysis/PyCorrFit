# -*- coding: utf-8 -*-
"""
Mixed components for fitting models.
"""

from __future__ import division


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


def triple_pnum(n,
                F1,
                F2,
                alpha21,
                alpha31,
                comp1,
                kwargs1,
                comp2,
                kwargs2,
                comp3,
                kwargs3
                ):
    u"""
    Double component models where the particle number is given in
    the model i.e. for confocal diffusion models.
    
    Parameters
    ----------
    n : float
        Total particle number
    F1, F2 : float
        Fraction of particle species 1 and 2.
        This infers that F3 = 1 - F1 - F2
    alpha21 : float
        Relative molecular brightness of particle
        2 compared to particle 1 (α₂₁ = q₂/q₁)
    alpha31 : float
        Relative molecular brightness of particle
        3 compared to particle 1
    comp1, comp2, comp3 : callables
        The model functions for each of the components.
    kwargs1, kwargs2, kwargs3 : dicts
        The keyword arguments for `comp1`, `comp2`, and `comp3`.
    """
    alpha11 = 1
    F3 = 1 - F1 - F2
    if F3 < 0:
        F3 = 0
    
    norm = (F1*alpha11 + F2*alpha21 + F3*alpha31)**2

    g1 = alpha11**2 * F1 * comp1(**kwargs1)
    g2 = alpha21**2 * F2 * comp2(**kwargs2)
    g3 = alpha31**2 * F3 * comp3(**kwargs3)
    
    G = 1/n * (g1 + g2 + g3) / norm
    
    return G