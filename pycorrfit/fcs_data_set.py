# -*- coding: utf-8 -*-
""" PyCorrFit data set

Classes for FCS data evaluation.
"""
from __future__ import print_function, division

import hashlib
import numpy as np
import scipy.interpolate as spintp
import scipy.optimize as spopt
import warnings

from . import models as mdls
from . import plotting

class Trace(object):
    """ unifies trace handling
    """
    def __init__(self, trace=None, countrate=None, duration=None,
                 name=None):
        """ Load trace data
        
        Parameters
        ----------
        trace : ndarray of shape (N, 2)
            The array contains time [s] and count rate [Hz].
        coutrate : float
            Average count rate [Hz].
            Mandatory if data is None. 
        duration : float
            Duration of measurement in seconds.
            Mandatory if data is None.
        name : str
            The name of the trace.
        """
        self._countrate = None
        self._duration = None
        self._trace = None
        self._uid = None
        
        if trace is None:
            self.countrate = countrate
            self.duration = duration
        else:
            self.trace = trace
        
        if name is None:
            name = "{:.2f}kHz, {:.0f}s".format(self.countrate/1000,
                                               self.duration)
        self.name = name
        
    @property
    def countrate(self):
        if self._countrate is None:
            self._countrate = self._trace[0,-1] - self._trace[0,0]
        return self._countrate
    
    @countrate.setter
    def countrate(self, value):
        assert value is not None, "Setting value with None forbidden!"
        assert self._trace is None, "Setting value impossible, "+\
                                    "if `self.trace` is set."
        self._countrate = value

    @property
    def duration(self):
        if not hasattr(self, "_duration"):
            self._duration = self._trace[0,-1] - self._trace[0,0]
        return self._duration
    
    @duration.setter
    def duration(self, value):
        assert value is not None, "Setting value with None forbidden!"
        assert self._trace is None, "Setting value impossible, "+\
                                    "if `self.trace` is set."
        self._duration = value
    
    @property
    def uid(self):
        if self._uid is None:
            hasher = hashlib.sha256()
            hasher.update(str(np.random.random()))
            hasher.update(str(self.trace))
            hasher.update(self.name)
            self._uid = hasher.hexdigest()
        return self._uid
    
    @property
    def trace(self):
        if self._trace is None:
            self._trace = np.array([ [0,             self.countrate],
                                     [self.duration, self.countrate] 
                                    ])
        return self._trace
    
    @trace.setter
    def trace(self, value):
        assert value is not None, "Setting value with None forbidden!"
        assert isinstance(value, np.ndarray), "value must be array!"
        assert value.shape[1] == 2, "shape of array must be (N,2)!"
        self._trace = value


class Correlation(object):
    """ unifies correlation curve handling
    """
    def __init__(self, backgrounds=[], correlation=None, corr_type="AC", 
                 filename=None, fit_algorithm="LevMar",
                 fit_model=None, fit_range=(0,-1),
                 fit_weight_data=None, fit_weight_type="none", 
                 normparm=None, title=None, traces=[]):
        """
        Parameters
        ----------
        backgrounds: list of instances of Trace
            background traces
        correlation: ndarray of shape (N,2)
            correlation data (time [s], correlation)
        corr_type: str
            type of correlation, e.g. "AC", "AC1", "cc12"
        filename: str
            path to filename of correlation
        fit_algorithm: str
            valid fit algorithm identifier (Algorithms.keys())
        fit_model: instance of FitModel
            the model used for fitting
        fit_range:
            fitting range in indices
        fit_weight_data: any
            data for the certain fit_weight_type
        normparm: int
            identifier of normalization parameter
        title: str
            user-editable title of this correlation
        traces: list of instances of Trace
            traces of the current correlation
        """
        # Todo:
        # - use fit parameters range for fitting
        # - set default values for fit_weight_memory
        # - implement shared data sets for global fit
        # - fit algorithm property setter: check for valid values with Algorithms.keys()
        # - self._fit_weight_memory: external weights
        # - Use existing Fit class below
        #   - change it to only accept one or more Correlation instances
        
        
        # must be created before setting properties
        self._correlation = None
        self._fit_algorithm = None   
        self._fit_model = None
        self._fit_parameters = None
        self._fit_parameters_range = None
        self._fit_parameters_variable = None
        self._fit_weight_memory = dict()
        self._model_memory = dict()

        self.backgrounds = backgrounds
        self.bg_correction_enabled = True
        if correlation is not None:
            self.correlation = correlation
        self.corr_type = corr_type
        self.filename = filename
        
        self.fit_algorithm = fit_algorithm
        self.fit_model = fit_model
        self.fit_range = fit_range
        # Do not change order:
        self.fit_weight_type = fit_weight_type
        self.fit_weight_parameters = fit_weight_data
    
        # lock prevents any changes to the parameters
        self.lock_parameters = False
        self.normparm = normparm
        self.title = title
        self.traces = traces

    @property
    def bg_correction_factor(self):
        """
        Returns background corrected version of
        self._correlation
        
        Notes
        -----
        Thompson, N. Lakowicz, J.;
        Geddes, C. D. & Lakowicz, J. R. (ed.)
        Fluorescence Correlation Spectroscopy
        Topics in Fluorescence Spectroscopy,
        Springer US, 2002, 1, 337-378
        """
        if not self.bg_correction_enabled:
            # bg correction disabled
            return 1

        if self.is_ac:
            # Autocorrelation
            if len(self.traces) == 1 and len(self.backgrounds) == 1:
                S = self.traces[0].countrate
                B = self.backgrounds[0].countrate
                bgfactor = (S/(S-B))**2
            else:
                warnings.warn("Correlation {}: no bg-correction".
                              format(self.uis))
                bgfactor = 1
        else:
            # Crosscorrelation
            if len(self.traces) == 2 and len(self.backgrounds) == 2:
                S = self.traces[0].countrate
                S2 = self.traces[1].countrate
                B = self.backgrounds[0].countrate
                B2 = self.backgrounds[1].countrate
                bgfactor = (S/(S-B)) * (S2/(S2-B2))
            else:
                warnings.warn("Correlation {}: no bg-correction".
                              format(self.uis))
                bgfactor = 1
        return bgfactor
    
    @property
    def correlation(self):
        """the correlation data, shape (N,2) with (time, correlation) """
        if self._correlation is not None:
            corr = self._correlation
            # perform background correction
            corr[:,1] *= self.bg_correction_factor
            return corr
    
    @correlation.setter
    def correlation(self, value):
        assert value is not None, "Setting value with None forbidden!"
        assert isinstance(value, np.ndarray), "value must be array!"
        assert value.shape[1] == 2, "shape of array must be (N,2)!"
        self._correlation = value

    @property
    def correlation_plot(self):
        """ returns correlation data for plotting (normalized, fit_ranged) """
        corr = self.correlation
        if corr is not None:
            # perform parameter normalization
            corr[:,1] *= self.normalize_factor
            return self.corr[:, self.fit_range[0]:self.fit_range[1]]
    
    @property
    def is_ac(self):
        """True if instance contains autocorrelation"""
        return self.corr_type.lower().count("ac") > 0

    @property
    def fit_is_weighted(self):
        """True if the current fit has weights"""
        if self.fit_weight_type == "none":
            return True
        else:
            return False

    @property
    def fit_model(self):
        """instance of a fit model"""
        return self._fit_model

    @fit_model.setter
    def fit_model(self, value):
        """set the fit model
        TODO: also allow model_id
        """
        if value != self._fit_model :
            self._fit_model = value
            # overwrite fitting parameters
            self._fit_parameters = self._fit_model.default_values
            self._fit_parameters_variables = self._fit_model.default_variables
            self._fit_parameters_range = np.zeros((len(self._fit_parameters, 2)))
            self.normalize_parm = None

    @property
    def fit_weight_data(self):
        """data of weighted fitting"""
        return self._fit_weight_memory[self.fit_weight_type]

    @fit_weight_data.setter
    def fit_weight_data(self, value):
        self._fit_weight_memory[self.fit_weight_type] = value

    @property
    def fit_parameters(self):
        """parameters that were fitted/will be used for fitting"""
        return self._fit_parameters

    @fit_parameters.setter
    def fit_parameters(self, value):
        if self.lock_parameters == False:
            self._fit_parameters = value
        else:
            warnings.warn("Correlation {}: fixed parameters unchanged.".
                          format(self.uid))
    
    @property
    def fit_parameters_range(self):
        """valid fitting ranges for fit parameters"""
        return self._fit_parameters_range

    @fit_parameters_range.setter
    def fit_parameters_range(self, value):
        assert self.value.shape[1] == 2
        assert value.shape[0] == self.fit_parameters.shape[0]
        self._fit_parameters_range = value

    @property
    def fit_parameters_variable(self):
        """which parameters are variable during fitting"""
        return self._fit_parameters_variable

    @fit_parameters_variable.setter
    def fit_parameters_variable(self, value):
        assert value.shape[0] == self.fit_parameters.shape[0]
        self._fit_parameters_variable = value

    @property
    def lag_time(self):
        """logarithmic lag time axis"""
        if self.correlation is not None:
            return self._correlation[:,0]
        else:
            # some default lag time
            return np.exp(np.linspace(np.log(1e-8),np.log(100)))

    @property
    def modeled(self):
        """fitted data values, same shape as self.correlation"""
        # perform parameter normalization
        return self.fit_model(self.fit_parameters, self.lag_time)

    @property
    def modeled_plot(self):
        """fitted data values, same shape as self.correlation_plot"""
        toplot = self.modeled[:, self.fit_range[0]:self.fit_range[1]].copy()
        toplot[:,1] *= self.normalize_factor
        return toplot

    @property
    def normalize_factor(self):
        """plot normalization according to self.normparm"""
        if self.normparm is None:
            # nothing to do
            return 1
        
        if self.normparm < self.fit_parameters.shape[0]:
            nfactor = self.fit_parameters[self.normparm]
        else:
            # get supplementary parameters
            alt = self.fit_model.get_supplementary_values(self.fit_parameters)
            nfactor = alt[self.normparm - self.fit_parameters.shape[0]:]
        
        return nfactor

    @property
    def residuals(self):
        """fit residuals, same shape as self.correlation"""
        residuals = self.correlation.copy()
        residuals[:,1] -= self.modeled[:,1]
        return residuals 
    
    @property
    def residuals_plot(self):
        """fit residuals, same shape as self.correlation_plot"""
        residuals_plot = self.correlation_plot.copy()
        residuals_plot[:,1] -= self.modeled_plot[:,1]
        return residuals_plot

    @property
    def uid(self):
        """unique identifier of this instance"""
        if self._uid is None:
            hasher = hashlib.sha256()
            hasher.update(str(np.random.random()))
            hasher.update(str(self.correlation))
            hasher.update(self.name)
            self._uid = hasher.hexdigest()
        return self._uid


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

