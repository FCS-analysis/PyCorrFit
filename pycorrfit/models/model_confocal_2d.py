import numpy as np

from .control import model_setup
from .cp_confocal import twod

# 2D simple gauss
def CF_Gxy_gauss(parms, tau):
    u""" Two-dimensional diffusion with a Gaussian laser profile.

        G(τ) = offset + 1/( n * (1+τ/τ_diff) )

        Calculation of diffusion coefficient and concentration
        from the effective radius of the detection profile (r₀ = 2*σ):
        D = r₀²/(4*τ_diff)
        Conc = n/(π*r₀²)

        *parms* - a list of parameters.
        Parameters (parms[i]):
        [0] n       Effective number of particles in confocal area
        [1] τ_diff  Characteristic residence time in confocal area
        [2] offset
        *tau* - lag time
    """
    n = parms[0]
    taudiff = parms[1]
    dc = parms[2]

    BB = twod(tau=tau, taudiff=taudiff)

    G = dc + 1/n * BB
    return G


def supplements(parms, countrate=None):
    # We can only give you the effective particle number
    n = parms[0]
    Info = list()
    if countrate is not None:
        # CPP
        cpp = countrate/n
        Info.append(["cpp [kHz]", cpp])
    return Info


parms = [4.0, 0.4, 0.0]

## boundaries
boundaries = [[0, np.inf]]*len(parms)
boundaries[-1] = [-np.inf, np.inf]

model_setup(
             modelid=6001,
             name="2D diffusion (confocal)",
             comp="2D",
             mtype="Confocal (Gaussian)",
             fctn=CF_Gxy_gauss,
             par_labels=[  u"n",
                           u"τ_diff [ms]",
                           u"offset"],
             par_values=parms,
             par_vary=[True, True, False],
             par_boundaries=boundaries,
             supplementary_method=supplements
            )
