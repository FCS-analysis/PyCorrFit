#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from os.path import abspath, dirname, split

import matplotlib.pylab as plt
import numpy as np
# Add parent directory to beginning of path variable
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import pycorrfit

from pycorrfit.fcs_data_set import Correlation, Fit

corr = Correlation()

tau = np.exp(np.linspace(np.log(1e-3),np.log(1e6), 100))
data = corr.fit_model(corr.fit_parameters, tau)
noise = (np.random.random(data.shape[0])-.5)*.0005
data += noise

corr.correlation = np.dstack((tau, data))[0]

fig, (ax1, ax2) = plt.subplots(2,1)
ax1.set_xscale("log")
ax2.set_xscale("log")

ax1.plot(corr.correlation_fit[:,0], corr.correlation_fit[:,1])
ax1.plot(corr.modeled_fit[:,0], corr.modeled_fit[:,1])

Fit(corr)

ax2.plot(corr.correlation_fit[:,0], corr.correlation_fit[:,1])
ax2.plot(corr.modeled_fit[:,0], corr.modeled_fit[:,1])

plt.show()

import IPython
IPython.embed()

# todo -> check outcome

