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
noise = np.random.random(data.shape[0])*.0005
data += noise

corr.correlation = np.dstack((tau, data))[0]

fig, ax = plt.subplots(1,1)
plt.plot(corr.correlation_fit[:,0], corr.correlation_fit[:,1])
plt.plot(corr.modeled_fit[:,0], corr.modeled_fit[:,1])

ax.set_xscale("log")
plt.show()

Fit(corr)

# todo -> check outcome

