import numpy as np

from pycorrfit.correlation import Correlation
from pycorrfit.fit import Fit


def create_corr():
    n = 2.4
    taud = 10
    SP = 3.3
    tau = np.exp(np.linspace(np.log(1e-3), np.log(1e6), 10))
    corr1 = Correlation(fit_model=6002)
    corr1.lag_time = tau
    # 0: n
    # 1: τ_diff [ms]
    p1a = corr1.fit_parameters.copy()
    p1b = p1a.copy()
    p1b[0] = n
    p1b[1] = taud
    # write values and return to original
    corr1.fit_parameters = p1b
    corr1.correlation = corr1.modeled_fit.copy()
    corr1.fit_parameters = p1a
    corr1.fit_parameters_variable = [True, True, False, False, False]

    corr2 = Correlation(fit_model=6011)
    corr2.lag_time = tau
    # 0: n
    # 3: τ_diff [ms]
    # 4: SP
    p2a = corr2.fit_parameters.copy()
    p2b = p2a.copy()
    p2b[0] = n
    p2b[3] = taud
    p2b[4] = SP
    # write values and return to original
    corr2.fit_parameters = p2b
    corr2.correlation = corr2.modeled_fit.copy()
    corr2.fit_parameters = p2a
    corr2.fit_parameters_variable = [True, False, False, True, True, False]

    corrs = [corr1, corr2]
    initparms = np.array([n, taud, SP])

    return corrs, initparms

def test_globalfit():
    corrs, initparms = create_corr()
    # commence global fit
    globalfit = Fit(correlations=corrs, global_fit=True)

    assert np.allclose(globalfit.fit_parm, initparms), "Global fit failed"


if __name__ == "__main__":
    test_globalfit()
