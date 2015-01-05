# -*- coding: utf-8 -*-
""" PyCorrFit data set

Classes for FCS data evaluation.
"""
from __future__ import print_function, division


import hashlib
import numpy as np

from . import models as mdls

class Background(object):
    """ A class to unify background handling
    """
    def __init__(self, coutrate=None, duration_s=None, trace=None,
                 identifier=None, name=None):
        """ Initiate a background.
        
        Parameters
        ----------
        coutrate : float
            Average countrate [Hz].
        duration_s : float
            Duration of measurement in seconds.
        trace : 2d `numpy.ndarray` of shape (N,2)
            The trace (time [s], countrate [Hz]).
            Overwrites `average` and `duration_s`
        name : str
            The name of the measurement.
        identifier : str
            A unique identifier. If not given, a sha256 hash will be
            created.
        
        """
        self.coutrate = coutrate
        self.duration_s = duration_s
        self.identifier = identifier
        self.name = name
            
        if trace is not None:
            self.trace = trace
            self.coutrate = np.average(trace[:,1])
            self.duration_s = trace[-1,0] - trace[0,0]
        
        ## Make sure all parameters have sensible values
        if self.duration_s is None:
            self.duration_s = 0
        
        if self.countrate is None:
            self.countrate = 0
        
        if self.trace is None:
            self.trace = np.zeros((2,2))
            self.trace[:,1] = self.countrate
            
        if name is None:
            self.name = "{:.2f kHz, {} s}".format(coutrate/1000,
                                                  self.duration_s)
        if identifier is None:
            hasher = hashlib.sha256()
            hasher.update(str(self.trace))
            hasher.update(self.name)
            self.identifier = hasher.hexdigest()            
            
           

class FCSDataSet(object):
    """ The class has all methods necessary for an FCS measurement.
    
    """
    def __init__(self, ac=None, trace=None, trace2=None,
                  ac2=None, cc12=None, cc21=None,
                  background1=None, background2=None):
        """ Initializes the FCS data set.
        
        All parms are 2d ndarrays of shape (N,2).
        
        """
        self.filename = None
        self.trace1 = trace
        self.trace2 = trace2
        self.ac1 = ac
        self.ac2 = ac2
        self.cc12 = cc12
        self.cc21 = cc21

        if background1 is not None:
            self.background1 = Background(trace = background1)
        if background2 is not None:
            self.background2 = background(trace = background2)

        self.InitComputeDerived()
        self.DoBackgroundCorrection()
        

    def EnableBackgroundCorrection(self, enable=True):
        """ Set to false to disable background correction.
        """
        self.UseBackgroundCorrection = enable
        
        
    def InitComputeDerived(self):
        """ Computes all parameters that can be derived from the
            correlation data and traces themselves.
        """
        # lenght of traces determines auto- or cross-correlation
        if self.cc12 is not None or self.cc21 is not None:
            self.IsCrossCorrelation = True
        else:
            self.IsCrossCorrelation = False
        if self.ac1 is not None or self.ac2 is not None:
            self.IsAutCorrelation = True
        else:
            self.IsAutCorrelation = False
        
        if self.trace1 is not None:
            self.duration1_s = self.trace1[-1,0] - self.trace1[0,0]
            self.countrate1 = np.average(self.trace1[:,1])
        else:
            self.countrate1 = None
            self.duration1_s = None

        if self.trace2 is not None:
            self.duration2_s = self.trace2[-1,0] - self.trace2[0,0]
            self.countrate2 = np.average(self.trace2[:,1])
        else:
            self.duration2_s = None
            self.countrate2 = None            


        # Initial fitting range is entire data set
        self.fit_range = {}
        names = ["ac1", "ac2", "cc12", "cc21"]
        for name in names:
            if hasattr(self, name):
                data = getattr(self, name)
                self.fit_range[name] = (data[0,0], data[-1,0])



    def DoBackgroundCorrection(self, data):
        """ Performs background correction.
        
        Notes
        -----
        Thompson, N. Lakowicz, J.;
        Geddes, C. D. & Lakowicz, J. R. (ed.)
        Fluorescence Correlation Spectroscopy
        Topics in Fluorescence Spectroscopy,
        Springer US, 2002, 1, 337-378
        """
        # Autocorrelation
        if ( not self.countrate1 in [0, None] and
             self.background1 is not None and
             self.ac1 is not None):
            S = self.countrate1
            B = self.background1.countrate
            # Calculate correction factor
            bgfactor = (S/(S-B))**2
            # set plotting data
            self.plot_ac1 = self.ac1 * bgfactor
        if ( not self.countrate2 in [0, None] and
             self.background2 is not None and
             self.ac2 is not None):
            S = self.countrate2
            B = self.background2.countrate
            # Calculate correction factor
            bgfactor = (S/(S-B))**2
            # set plotting data
            self.plot_ac2 = self.ac2 * bgfactor            
        
        # Crosscorrelation
        if ( not self.countrate1 in [0, None] and
             not self.countrate2 in [0, None] and
             self.background1 is not None and
             self.background2 is not None and
             self.IsCrossCorrelation
           )
            S = self.countrate1
            S2 = self.countrate2
            B = self.background1.countrate1
            B2 = self.background1.countrate2
            bgfactor = (S/(S-B)) * (S2/(S2-B2))
            if self.cc12 is not None:
                self.plot_cc12 = self.cc12 * bgfactor 
            if self.cc21 is not None:
                self.plot_cc21 = self.cc21 * bgfactor             
            

    def GetBackground(self):
        """ Returns the backgrounds of the data set.
        """
        return self.background1, self.background2
        
    
    def GetPlotCorrelation(self):
        """ Returns a dictionary with correlation curves.
        
        Keys may include "ac1", "ac2", "cc12", "cc21" as well as
        "ac1_fit", "ac2_fit", "cc12_fit", "cc21_fit".
        """
        if self.UseBackgroundCorrection:
            self.DoBackgroundCorrection()
    
        result = dict()
        
        names = ["ac1", "ac2", "cc12", "cc21"]
        
        for name in names:
            if not hasattr(self, "plot_"+name):
                rawdata = getattr(self, name)
                if rawdata is not None:
                    result[name] = rawdata.copy()
            else:
                plotdata = getattr(self, name)
                result[name] = plotdata.copy()
            if hasattr(self, "plot_"+name+"_fit"):
                fitted = getattr(self, "plot_"+name+"_fit")
                result[name+"_fit"] = fitted.copy()

        return result


    def SetBackground(self, bgac1=None, bgac2=None):
        """ Set the background of the measurement.
        
        `bg*` is an instance of `pycorrfit.Background`.
        """
        #if isinstance(background, Background):
        #    self.background = bg
        #elif isinstance(background, list)
        self.background1 = bgac1
        self.background2 = bgac2


    def SetFitRange(self, start, end, components=None):
        """ Set the range for fitting a correlation curve.
        
        The unit is seconds.
        
        Exapmles
        --------
        SetFitRange(.2, 1)
        SetFitRange(.4, .7, ["ac2", "cc12"])
        """
        if components is not None:
            self.fit_range = {"ac1" : (start,end),
                              "ac2" : (start,end),
                              "cc12": (start,end),
                              "cc21": (start,end)  }
        else:
            for cc in components:
                self.fitrange[cc] = (start,end)
            


class Fit(object):
    """ Used for fitting FCS data to models.
    """
    def __init__(self, raw_data, model_id, model_parms=None,
                 fit_bool=None, fit_ival=None, fit_ival_is_index=False,
                 weight_type="none", weight_spread=0, weights=None,
                 fit_algorithm="Lev-Mar",
                 verbose=False, uselatex=False):
        """ Using an FCS model, fit the data of shape (N,2).


        Parameters
        ----------
        raw_data : 2d `numpy.ndarray` of shape (2,N)
            The data to which should be fitted. The first column
            contains the x data (time in s). The second column contains
            the y values (correlation data).
        mode_lid : int
            Modelid as in `pycorrfit.models.modeldict.keys()`.
        model_parms : array-type of length P
            The initial parameters for the specific model.
        fit_bool : bool array of length P
            Defines the model parameters that are variable (True) or
            fixed (False) durin fitting.
        fit_ival : tuple
            Interval of x values for fitting given in seconds or by
            indices (see `fit_ival_is_index`). If the discrete array
            does not match the interval, then the index closer towards
            the center of the interval is used.
        fit_ival_is_index : bool
            Set to `True` if `fit_ival` is given in indices instead of
            seconds.
        weight_type : str
            Type of weights. Should be one of

                - 'none' (standard) : no weights.
                - 'splineX' : fit a Xth order spline and calulate standard
                        deviation from that difference
                - 'model function' : calculate std. dev. from difference
                        of fit function and dataexpfull.
                - 'other' - use `weights`
        
        weight_spread : int
            Number of values left and right from a data point to include
            to weight a data point. The total number of points included
            is 2*`weight_spread` + 1.
        weights : 1d `numpy.ndarray` of length (N)
            Weights to use when `weight_type` is set to 'other'.
        fit_algorithm : str
            The fitting algorithm to be used for minimization. Have a
            look at the PyCorrFit documentation for more information.
            Should be one of

                - 'Lev-Mar' : Least squares minimization
                - 'Nelder-Mead' : Simplex
                - 'BFGS' : quasi-Newton method of Broyden,
                         Fletcher, Goldfarb and Shanno
                - 'Powell'
                - 'Polak-Ribiere'
        verbose : int
            Increase verbosity by incrementing this number.
        uselatex : bool
            If verbose > 0, plotting will be performed with LaTeX.
        """
        self.y_full = raw_data[:,1].copy()
        self.x_full = raw_data[:,0] * 1000 # convert to ms
        
        # model function
        self.func = mdls.GetModelFunctionFromId(model_id)
        
        # fit parameters
        if model_parms is None:
            model_parms = mdls.GetModelParametersFromId(model_id)
        self.model_parms = model_parms
        self.model_parms_initial = 1*model_parms
        
        # values to fit
        if fit_bool is None:
            fit_bool = mdls.GetModelFitBoolFromId(model_id)
        assert len(fit_bool) == len(model_parms)
        self.fit_bool = fit_bool

        # fiting interval
        if fit_ival is None:
            fit_ival = (self.x[0], self.x[-1])
        assert fit_ival[0] < fit_ival[1]
        self.fit_ival = fit_ival
        
        self.fit_ival_is_index = fit_ival_is_index
        
        
        # weight type
        assert weight_type.strip("1234567890") in ["none", "spline",
                                              "model function", "other"]
        self.weight_type = weight_type
        
        # weight spread
        assert int(weight_spread) >= 0
        self.weight_spread = int(weight_spread)
        
        # weights
        if weight_type == "other":
            assert isinstance(weights, np.ndarray)        
        self.weights = weights

        self.fit_algorithm = fit_algorithm
        self.verbose = verbose
        self.uselatex = uselatex

        self.ComputetXYArrays()
        self.ComputeWeights()

        
    def ComputeXYArrays(self):
        """ Determine the fitting interval and set `self.x` and `self.y`
        
        Sets:
        self.x
        self.y
        self.fit_ival_index
        """
        if not self.fit_ival_is_index:
            # we need to compute the indices that are inside the
            # fitting interval.
            #
            # interval in seconds:
            # self.ival
            #
            # x values:
            # self.x
            #
            start = np.sum(self.x <= self.ival[0]) - 1 
            end = self.x.shape[0] - np.sum(self.x >= self.ival[1])
            self.fit_ival_index = (start, end)
        else:
            self.fit_ival_index = start, end = self.fit_ival
        # We now have two values. Both values will be included in the
        # cropped arrays.
        self.x = self.x_full[start:end+1]
        self.y = self.y_full[start:end+1]


    def ComputeWeights(self):
        """ Determines if we have weights and computes them.
         
        sets
        - self.fit_weights
        - self.is_weighted_fit
        """
        ival = self.fit_ival_index
        weight_spread = self.weight_spread
        weight_type = self.weight_type

        # some frequently used lengths
        datalen = self.x.shape[0]
        datalenfull = self.x_full.shape[0]        
        # Calculated dataweights
        dataweights = np.zeros(datalen)

        self.is_weighted_fit = True # will be set to False if not weights

        if weight_type[:6] == "spline":
            # Number of knots to use for spline
            try:
                knotnumber = int(weight_type[6:])
            except:
                if self.verbose > 1:
                    print("Could not get knot number. Setting it to 5.")
                knotnumber = 5

            # Compute borders for spline fit.
            if ival[0] < weight_spread:
                # optimal case
                pmin = ival[0]
            else:
                # non-optimal case
                # we need to cut pmin
                pmin = weight_spread
            if datalenfull - ival[1] < weight_spread:
                # optimal case
                pmax = datalenfull - ival[1]
            else:
                # non-optimal case
                # we need to cut pmax
                pmax = weight_spread
            x = self.x_full[ival[0]-pmin:ival[1]+pmax]
            y = self.y_full[ival[0]-pmin:ival[1]+pmax]
            # we are fitting knots on a base 10 logarithmic scale.
            xs = np.log10(x)
            knots = np.linspace(xs[1], xs[-1], knotnumber+2)[1:-1]
            try:
                tck = spintp.splrep(xs, y, s=0, k=3, t=knots, task=-1)
                ys = spintp.splev(xs, tck, der=0)
            except:
                if self.verbose > 0:
                    raise ValueError("Could not find spline fit with "+\
                                     "{} knots.".format(knotnumber))
                return
            if self.verbose > 0:
                try:
                    # If plotting module is available:
                    name = "Spline fit: "+str(knotnumber)+" knots"
                    plotting.savePlotSingle(name, 1*x, 1*y, 1*ys,
                                             dirname=".",
                                             uselatex=self.uselatex)
                except:
                    # use matplotlib.pylab
                    try:
                        from matplotlib import pylab as plt
                        plt.xscale("log")
                        plt.plot(x, ys, x, y)
                        plt.show()
                    except ImportError:
                        # Tell the user to install matplotlib
                        print("Couldn't import pylab! - not Plotting")

            ## Calculation of variance
            # In some cases, the actual cropping interval from ival[0]
            # ro ival[1] is chosen, such that the dataweights must be
            # calculated from unknown datapoints.
            # (e.g. points+endcrop > len(dataexpfull)
            # We deal with this by multiplying dataweights with a factor
            # corresponding to the missed points.
            for i in range(datalen):
                # Define start and end positions of the sections from
                # where we wish to calculate the dataweights.
                # Offset at beginning:
                if  i + ival[0] <  weight_spread:
                    # The offset that occurs
                    offsetstart = weight_spread - i - ival[0]
                    offsetcrop = 0
                elif ival[0] > weight_spread:
                    offsetstart = 0
                    offsetcrop = ival[0] - weight_spread
                else:
                    offsetstart = 0
                    offsetcrop = 0
                # i: counter on dataexp array
                # start: counter on y array
                start = i - weight_spread + offsetstart + ival[0] - offsetcrop
                end = start + 2*weight_spread + 1 - offsetstart
                dataweights[i] = (y[start:end] - ys[start:end]).std()
                # The standard deviation at the end and the start of the
                # array are multiplied by a factor corresponding to the
                # number of bins that were not used for calculation of the
                # standard deviation.
                if offsetstart != 0:
                    reference = 2*weight_spread + 1
                    dividor = reference - offsetstart
                    dataweights[i] *= reference/dividor   
                # Do not substitute len(y[start:end]) with end-start!
                # It is not the same!
                backset =  2*weight_spread + 1 - len(y[start:end]) - offsetstart
                if backset != 0:
                    reference = 2*weight_spread + 1
                    dividor = reference - backset
                    dataweights[i] *= reference/dividor
        elif weight_type == "model function":
            # Number of neighbouring (left and right) points to include
            if ival[0] < weight_spread:
                pmin = ival[0]
            else:
                pmin = weight_spread
            if datalenfull - ival[1] <  weight_spread:
                pmax = datalenfull - self.ival[1]
            else:
                pmax = weight_spread
            x = self.x_full[ival[0]-pmin:ival[1]+pmax]
            y = self.y_full[ival[0]-pmin:ival[1]+pmax]
            # Calculated dataweights
            for i in np.arange(datalen):
                # Define start and end positions of the sections from
                # where we wish to calculate the dataweights.
                # Offset at beginning:
                if  i + ival[0] <  weight_spread:
                    # The offset that occurs
                    offsetstart = weight_spread - i - ival[0]
                    offsetcrop = 0
                elif ival[0] > weight_spread:
                    offsetstart = 0
                    offsetcrop = ival[0] - weight_spread
                else:
                    offsetstart = 0
                    offsetcrop = 0
                # i: counter on dataexp array
                # start: counter on dataexpfull array
                start = i - weight_spread + offsetstart + ival[0] - offsetcrop
                end = start + 2*weight_spread + 1 - offsetstart
                #start = ival[0] - weight_spread + i
                #end = ival[0] + weight_spread + i + 1
                diff = y - self.func(self.model_parms, x)
                dataweights[i] = diff[start:end].std()
                # The standard deviation at the end and the start of the
                # array are multiplied by a factor corresponding to the
                # number of bins that were not used for calculation of the
                # standard deviation.
                if offsetstart != 0:
                    reference = 2*weight_spread + 1
                    dividor = reference - offsetstart
                    dataweights[i] *= reference/dividor   
                # Do not substitute len(diff[start:end]) with end-start!
                # It is not the same!
                backset =  2*weight_spread + 1 - len(diff[start:end]) - offsetstart
                if backset != 0:
                    reference = 2*weight_spread + 1
                    dividor = reference - backset
                    dataweights[i] *= reference/dividor
        elif self.fittype == "other":
            # This means that the user knows the dataweights and already
            # gave it to us.
            assert self.weights is not None
            
            # Check if these other weights have length of the cropped
            # or the full array.
            if len(self.weights) == datalen:
                dataweights = self.weights
            elif len(self.weights) == datalenfull:
                dataweights = self.weights[ival[0], ival[1]+1]
            else:
                raise ValueError, \
                  "`weights` must have length of full or cropped array."
        else:
            # The fit.Fit() class will divide the function to minimize
            # by the dataweights only if we have weights
            self.is_weighted_fit = False
        
        self.fit_weights = dataweights
        

    def fit_func(self, parms, x):
        """ Create the function to be minimized. The old function
            `function` has more parameters than we need for the fitting.
            So we use this function to set only the necessary 
            parameters. Returns what `function` would have done.
        """
        # We reorder the needed variables to only use these that are
        # not fixed for minimization
        index = 0
        for i in np.arange(len(self.model_parms)):
            if self.fit_bool[i]:
                self.model_parms[i] = parms[index]
                index = index + 1
        # Only allow physically correct parameters
        self.model_parms = self.check_parms(self.model_parms)
        tominimize = (self.func(self.model_parms, x) - self.y)
        # Check if we have a weighted fit
        if self.is_weighted_fit:
            # Check dataweights for zeros and don't use these
            # values for the least squares method.
            with np.errstate(divide='ignore'):
                tominimize = np.where(self.fit_weights!=0, 
                                      tominimize/self.fit_weights, 0)
            ## There might be NaN values because of zero weights:
            #tominimize = tominimize[~np.isinf(tominimize)]
        return tominimize


    def fit_function_scalar(self, parms, x):
        """
            Wrapper of `fit_function` for scalar minimization methods.
            Returns the sum of squares of the input data.
            (Methods that are not "Lev-Mar")
        """
        e = self.fit_func(parms,x)
        return np.sum(e*e)


    def get_chi_squared(self):
        """
            Calculate Chi² for the current class.
        """
        # Calculate degrees of freedom
        dof = len(self.x) - len(self.model_parms) - 1
        # This is exactly what is minimized by the scalar minimizers
        chi2 = self.fit_function_scalar(self.model_parms, self.x)
        return chi2 / dof


    def minimize(self):
        """ This will minimize *self.fit_function()* using least squares.
            *self.values*: The values with which the function is called.
            *valuestofit*: A list with bool values that indicate which values
            should be used for fitting.
            Function *self.fit_function()* takes two parameters:
            self.fit_function(parms, x) where *x* are x-values of *dataexp*.
        """
        assert (np.sum(self.fit_bool) == 0), "No parameter selected for fitting."

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
        parmoptim = res[0]

        # Now write the optimal parameters to our values:
        index = 0
        for i in range(len(self.model_parms)):
            if self.valuestofit[i]:
                self.model_parms[i] = parmoptim[index]
                index = index + 1
        # Only allow physically correct parameters
        self.model_parms = self.check_parms(self.model_parms)
        # Write optimal parameters back to this class.

        self.chi = self.get_chi_squared()
        
        # Compute error estimates for fit (Only "Lev-Mar")
        if self.fit_algorithm == "Lev-Mar":
            # This is the standard way to minimize the data. Therefore,
            # we are a little bit more verbose.
            if res[4] not in [1,2,3,4]:
                warnings.warn("Optimal parameters not found: " + res[3])
            try:
                self.covar = res[1] * self.chi # The covariance matrix
            except:
                warnings.warn("PyCorrFit Warning: Error estimate not "+\
                              "possible, because we could not "+\
                              "calculate covariance matrix. Please "+\
                              "try reducing the number of fitting "+\
                              "parameters.")
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

