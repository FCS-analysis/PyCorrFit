# -*- coding: utf-8 -*-
""" PyCorrFit

    Module fitting
    Here are the necessary functions for computing a fit with given parameters.
    See included class "Fit" for more information.

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

try:
    import matplotlib.pyplot as plt
except:
    pass
    
import numpy as np
from scipy import interpolate as spintp
from scipy import optimize as spopt

# If we use this module with PyCorrFit, we can plot things with latex using
# our own special thing.
try:
    from . import plotting
except:
    pass


class Fit(object):
    """
        The class Fit needs the following parameters to perform a fit:
        check_parms - A function checking the parameters for plausibility.
        dataexpfull - Full experimental data *array of tuples*
        function - function to be used for fitting f(parms, x) 
        interval - interval of dataexpfull to fit in. [a, b]
        values - starting parameters *parms* for fitting. *array*
        valuestofit - which parameter to use for fitting. *bool array*
        weights - no. of datapoints from left and right to use for weighting
        fittype - type of fit. Can be one of the following
                  - "None" (standard) - no weights. (*weights* is ignored)
                  - "splineX" - fit a Xth order spline and calulate standard
                               deviation from that difference
                  - "model function" - calculate std. dev. from difference
                                        of fit function and dataexpfull.
                  - "other" - use an external std. dev.. The variable
                              self.external_deviations has to be set before
                              self.ApplyParameters is called. Cropping with
                              *interval* is performed here.
        fit_algorithm - The fitting algorithm to be used for minimization
                        Have a look at the PyCorrFit documentation for more
                        information.
                        - "Lev-Mar" Least squares minimization
                        - "Nelder-Mead" Simplex
                        - "BFGS" quasi-Newton method of Broyden,
                                 Fletcher, Goldfarb and Shanno
                        - "Powell"
                        - "Polak-Ribiere"
    """
    def __init__(self):
        """ Initial setting of needed variables via the given *fitset* """   
        self.check_parms = None
        self.dataexpfull = None
        self.function = None
        self.interval = None
        # Eventually use latex. This is passed
        # to each plotting command. Only when plotting
        # module is available.
        self.uselatex = False 
        self.values = None
        self.valuestofit = None

        self.verbose = False # Verbose mode (shows e.g. spline fit)
        # The weights (data points from left and right of data array) have
        # to be chosen in a way, that the interval +/- weights will not
        # exceed self.dataexpfull!!!!
        self.weights = None
        # Changing fittype will change calculation of variances=dataweights**2.
        # None means dataweights is 1.
        self.fittype = "None"
        # Chi**2 Value
        self.chi = None
        # Messages from fit algorithm
        self.mesg = None
        # Optimal parameters found by fit algorithm
        self.parmoptim = None
        self.covar = None # covariance matrix 
        self.parmoptim_error = None # Errors of fit
        # Variances for fitting
        self.dataweights = None
        # External std defined by the user
        self.external_deviations = None
        # It is possible to edit tolerance for fitting
        # ftol, xtol and gtol.
        # Those parameters could be added to the fitting routine later.
        # Should we do a weighted fit?
        # Standard is yes. If there are no weights
        # (self.fittype not set) then this value becomes False
        self.weightedfit=True
        # Set the standard method for minimization
        self.fit_algorithm = "Lev-Mar"
        


    def ApplyParameters(self):
        if self.interval is None:
            self.startcrop = self.endcrop = 0
        else:
            [self.startcrop, self.endcrop] = self.interval
        # Get self.dataexp
        if self.startcrop == self.endcrop:
            self.dataexp = 1*self.dataexpfull
            self.startcrop = 0
            self.endcrop = len(self.dataexpfull)
        else:
            self.dataexp = 1*self.dataexpfull[self.startcrop:self.endcrop]
            # If startcrop is larger than the lenght of dataexp,
            # We will not have an array. Prevent that.
            if len(self.dataexp) == 0:
                self.dataexp = 1*self.dataexpfull
        # Calculate x-values
        # (Extract tau-values from dataexp)
        self.x = self.dataexp[:, 0]
        # Experimental data
        self.data = self.dataexp[:,1]
        # Set fit parameters
        self.fitparms = np.zeros(sum(self.valuestofit))
        index = 0
        for i in np.arange(len(self.values)):
            if self.valuestofit[i]:
                self.fitparms[index] = np.float(self.values[i])
                index = index + 1
        # Assume we have a weighted fit. If this is not the case then
        # this is changed in the else statement of the following 
        # "if"-statement:
        self.weightedfit=True
        if self.fittype[:6] == "spline":
            # Number of knots to use for spline
            try:
                knotnumber = int(self.fittype[6:])
            except:
                print "Could not get knotnumber. Setting to 5."
                knotnumber = 5
            # Number of neighbouring (left and right) points to include
            points = self.weights
            # Calculated dataweights
            datalen = len(self.dataexp[:,1])
            dataweights = np.zeros(datalen)
            if self.startcrop < points:
                pmin = self.startcrop
            else:
                pmin = points
            if len(self.dataexpfull) - self.endcrop <  points:
                pmax = (len(self.dataexpfull) - self.endcrop)
            else:
                pmax = points
            x = self.dataexpfull[self.startcrop-pmin:self.endcrop+pmax,0]
            xs = np.log10(x)
            y = self.dataexpfull[self.startcrop-pmin:self.endcrop+pmax,1]
            knots = np.linspace(xs[1], xs[-1], knotnumber+2)[1:-1]
            try:
                tck = spintp.splrep(xs,y,s=0,k=3,t=knots,task=-1)
                ys = spintp.splev(xs,tck,der=0)
            except:
                print "Could not find spline with "+str(knotnumber)+" knots."
                return
            if self.verbose == True:
                try:
                    # If plotting module is available:
                    name = "Spline fit: "+str(knotnumber)+" knots"
                    plotting.savePlotSingle(name, 1*x, 1*y, 1*ys, dirname = ".",
                                            uselatex=self.uselatex)
                except:
                    try:
                        plt.xscale("log")
                        plt.plot(x,ys, x,y)
                        plt.show()
                    except ImportError:
                        # Tell the user to install matplotlib
                        print "Matplotlib not found!"
                        
            ## Calculation of variance
            # In some cases, the actual cropping interval from self.startcrop to
            # self.endcrop is chosen, such that the dataweights must be
            # calculated from unknown datapoints.
            # (e.g. points+endcrop > len(dataexpfull)
            # We deal with this by multiplying dataweights with a factor
            # corresponding to the missed points.
            for i in np.arange(datalen):
                # Define start and end positions of the sections from
                # where we wish to calculate the dataweights.
                # Offset at beginning:
                if  i + self.startcrop <  points:
                    # The offset that occurs
                    offsetstart = points - i - self.startcrop
                    offsetcrop = 0
                elif self.startcrop > points:
                    offsetstart = 0
                    offsetcrop = self.startcrop - points
                else:
                    offsetstart = 0
                    offsetcrop = 0
                # i: counter on dataexp array
                # start: counter on y array
                start = i - points + offsetstart + self.startcrop - offsetcrop
                end = start + 2*points + 1 - offsetstart
                dataweights[i] = (y[start:end] - ys[start:end]).std()
                # The standard deviation at the end and the start of the
                # array are multiplied by a factor corresponding to the
                # number of bins that were not used for calculation of the
                # standard deviation.
                if offsetstart != 0:
                    reference = 2*points + 1
                    dividor = reference - offsetstart
                    dataweights[i] *= reference/dividor   
                # Do not substitute len(y[start:end]) with end-start!
                # It is not the same!
                backset =  2*points + 1 - len(y[start:end]) - offsetstart
                if backset != 0:
                    reference = 2*points + 1
                    dividor = reference - backset
                    dataweights[i] *= reference/dividor
        elif self.fittype == "model function":
            # Number of neighbouring (left and right) points to include
            points = self.weights
            if self.startcrop < points:
                pmin = self.startcrop
            else:
                pmin = points
            if len(self.dataexpfull) - self.endcrop <  points:
                pmax = (len(self.dataexpfull) - self.endcrop)
            else:
                pmax = points
            x = self.dataexpfull[self.startcrop-pmin:self.endcrop+pmax,0]
            y = self.dataexpfull[self.startcrop-pmin:self.endcrop+pmax,1]
            # Calculated dataweights
            datalen = len(self.dataexp[:,1])
            dataweights = np.zeros(datalen)
            for i in np.arange(datalen):
                # Define start and end positions of the sections from
                # where we wish to calculate the dataweights.
                # Offset at beginning:
                if  i + self.startcrop <  points:
                    # The offset that occurs
                    offsetstart = points - i - self.startcrop
                    offsetcrop = 0
                elif self.startcrop > points:
                    offsetstart = 0
                    offsetcrop = self.startcrop - points
                else:
                    offsetstart = 0
                    offsetcrop = 0
                # i: counter on dataexp array
                # start: counter on dataexpfull array
                start = i - points + offsetstart + self.startcrop - offsetcrop
                end = start + 2*points + 1 - offsetstart
                #start = self.startcrop - points + i
                #end = self.startcrop + points + i + 1
                diff = y - self.function(self.values, x)
                dataweights[i] = diff[start:end].std()
                # The standard deviation at the end and the start of the
                # array are multiplied by a factor corresponding to the
                # number of bins that were not used for calculation of the
                # standard deviation.
                if offsetstart != 0:
                    reference = 2*points + 1
                    dividor = reference - offsetstart
                    dataweights[i] *= reference/dividor   
                # Do not substitute len(diff[start:end]) with end-start!
                # It is not the same!
                backset =  2*points + 1 - len(diff[start:end]) - offsetstart
                if backset != 0:
                    reference = 2*points + 1
                    dividor = reference - backset
                    dataweights[i] *= reference/dividor
        elif self.fittype == "other":
            # This means that the user knows the dataweights and already
            # gave it to us.
            if self.external_deviations is not None:
                dataweights = \
                           self.external_deviations[self.startcrop:self.endcrop]
            else:
                raise ValueError, \
                      "self.external_deviations not set for fit type 'other'."
        else:
            # The fit.Fit() class will divide the function to minimize
            # by the dataweights only if we have weights
            self.weightedfit=False
            dataweights=None
        self.dataweights = dataweights


    def fit_function(self, parms, x):
        """ Create the function to be minimized. The old function
            `function` has more parameters than we need for the fitting.
            So we use this function to set only the necessary 
            parameters. Returns what `function` would have done.
        """
        # We reorder the needed variables to only use these that are
        # not fixed for minimization
        index = 0
        for i in np.arange(len(self.values)):
            if self.valuestofit[i]:
                self.values[i] = parms[index]
                index = index + 1
        # Only allow physically correct parameters
        self.values = self.check_parms(self.values)
        tominimize = (self.function(self.values, x) - self.data)
        # Check if we have a weighted fit
        if self.weightedfit is True:
            # Check dataweights for zeros and don't use these
            # values for the least squares method.
            with np.errstate(divide='ignore'):
                tominimize = np.where(self.dataweights!=0, 
                                      tominimize/self.dataweights, 0)
            ## There might be NaN values because of zero weights:
            #tominimize = tominimize[~np.isinf(tominimize)]
        return tominimize


    def fit_function_scalar(self, parms, x):
        """
            Wrapper of `fit_function` for scalar minimization methods.
            Returns the sum of squares of the input data.
            (Methods that are not "Lev-Mar")
        """
        e = self.fit_function(parms,x)
        return np.sum(e*e)
        

    def get_chi_squared(self):
        """
            Calculate Chi² for the current class.
        """
        # Calculate degrees of freedom
        dof = len(self.x) - len(self.parmoptim) - 1
        # This is exactly what is minimized by the scalar minimizers
        chi2 = self.fit_function_scalar(self.parmoptim, self.x)
        return chi2 / dof


    def minimize(self):
        """ This will minimize *self.fit_function()* using least squares.
            *self.values*: The values with which the function is called.
            *valuestofit*: A list with bool values that indicate which values
            should be used for fitting.
            Function *self.fit_function()* takes two parameters:
            self.fit_function(parms, x) where *x* are x-values of *dataexp*.
        """
        if np.sum(self.valuestofit) == 0:
            print "No fitting parameters selected."
            self.valuesoptim = 1*self.values
            return
        # Get algorithm
        algorithm = Algorithms[self.fit_algorithm][0]

        # Begin fitting
        if self.fit_algorithm == "Lev-Mar":
            res = algorithm(self.fit_function, self.fitparms[:],
                            args=(self.x), full_output=1)
        else:
            res = algorithm(self.fit_function_scalar, self.fitparms[:],
                            args=([self.x]), full_output=1)

        # The optimal parameters
        self.parmoptim = res[0]

        # Now write the optimal parameters to our values:
        index = 0
        for i in range(len(self.values)):
            if self.valuestofit[i]:
                self.values[i] = self.parmoptim[index]
                index = index + 1
        # Only allow physically correct parameters
        self.values = self.check_parms(self.values)
        # Write optimal parameters back to this class.
        self.valuesoptim = 1*self.values # This is actually a redundance array
        self.chi = self.get_chi_squared()
        
        # Compute error estimates for fit (Only "Lev-Mar")
        if self.fit_algorithm == "Lev-Mar":
            # This is the standard way to minimize the data. Therefore,
            # we are a little bit more verbose.
            if res[4] not in [1,2,3,4]:
                print "Optimal parameters not found: " + res[3]
            try:
                self.covar = res[1] * self.chi # The covariance matrix
            except:
                print "PyCorrFit Warning: Error estimate not possible, because we"
                print "          could not calculate covariance matrix. Please try"
                print "          reducing the number of fitting parameters."
                self.parmoptim_error = None
            else:
                # Error estimation of fitted parameters
                if self.covar is not None:
                    self.parmoptim_error = np.diag(self.covar)
        else:
            self.parmoptim_error = None


def GetAlgorithmStringList():
    """
        Get supported fitting algorithms as strings.
        Returns two lists (that are key-sorted) for key and string.
    """
    A = Algorithms
    out1 = list()
    out2 = list()
    a = list(A.keys())
    a.sort()
    for key in a:
        out1.append(key)
        out2.append(A[key][1])
    return out1, out2
    

# As of version 0.8.3, we support several minimization methods for
# fitting data to experimental curves.
# These functions must be callable like scipy.optimize.leastsq. e.g.
# res = spopt.leastsq(self.fit_function, self.fitparms[:],
#                     args=(self.x), full_output=1)
Algorithms = dict()

# the original one is the least squares fit "leastsq"
Algorithms["Lev-Mar"] = [spopt.leastsq, 
           "Levenberg-Marquardt"]

# simplex 
Algorithms["Nelder-Mead"] = [spopt.fmin,
           "Nelder-Mead (downhill simplex)"]

# quasi-Newton method of Broyden, Fletcher, Goldfarb, and Shanno
Algorithms["BFGS"] = [spopt.fmin_bfgs,
           "BFGS (quasi-Newton)"]

# modified Powell-method
Algorithms["Powell"] = [spopt.fmin_powell,
           "modified Powell (conjugate direction)"]

# nonliner conjugate gradient method by Polak and Ribiere
Algorithms["Polak-Ribiere"] = [spopt.fmin_cg,
           "Polak-Ribiere (nonlinear conjugate gradient)"]

