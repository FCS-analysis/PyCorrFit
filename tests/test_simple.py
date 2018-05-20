import numpy as np

import pycorrfit  # @UnusedImport
from pycorrfit.correlation import Correlation
from pycorrfit.fit import Fit


def create_corr():
    corr = Correlation()

    tau = np.exp(np.linspace(np.log(1e-3), np.log(1e6), 10))
    data = corr.fit_model(corr.fit_parameters, tau)
    noise = (np.random.random(data.shape[0])-.5)*.0005
    data += noise

    corr.correlation = np.dstack((tau, data))[0]
    return corr


def test_simple_corr():
    corr = create_corr()
    oldparms = corr.fit_parameters.copy()
    temp = corr.fit_parameters
    temp[0] *= 2
    temp[-1] *= .1

    Fit(corr)

    res = oldparms - corr.fit_parameters

    assert np.allclose(res, np.zeros_like(res), atol=0.010)


if __name__ == "__main__":
    import matplotlib.pylab as plt
    corr = create_corr()

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.set_xscale("log")
    ax2.set_xscale("log")

    print(corr.fit_parameters)
    temp = corr.fit_parameters
    temp[0] *= 2
    temp[-1] *= .1
    ax1.plot(corr.correlation_fit[:, 0], corr.correlation_fit[:, 1])
    ax1.plot(corr.modeled_fit[:, 0], corr.modeled_fit[:, 1])
    print(corr.fit_parameters)

    Fit(corr)

    print(corr.fit_parameters)

    ax2.plot(corr.correlation_fit[:, 0], corr.correlation_fit[:, 1])
    ax2.plot(corr.modeled_fit[:, 0], corr.modeled_fit[:, 1])

    plt.show()
