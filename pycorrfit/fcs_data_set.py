# -*- coding: utf-8 -*-
""" PyCorrFit data set

Classes for FCS data evaluation.
"""
from __future__ import print_function, division

import copy
import hashlib
import lmfit
import numpy as np
import scipy.integrate as spintg
import scipy.interpolate as spintp
import warnings

from . import models as mdls

class Trace(object):
    """ unifies trace handling
    """
    def __init__(self, trace=None, countrate=None, duration=None,
                 name=None):
        """ Load trace data
        
        Parameters
        ----------
        trace : ndarray of shape (N, 2)
            The array contains time [ms] and count rate [kHz].
        coutrate : float
            Average count rate [kHz].
            Mandatory if `trace` is None. 
        duration : float
            Duration of measurement in milliseconds.
            Mandatory if `trace` is None.
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
            name = "{:.2f}kHz, {:.0f}s".format(self.countrate,
                                               self.duration/1000)
        self.name = name
    
    def __getitem__(self, idx):
        return self.trace[idx]
    
    def __repr__(self):
        text = "Trace of length {:.3f}s and countrate {:.3f}kHz".format(
                self.duration/1000, self.countrate)
        return text
    
    @property
    def countrate(self):
        if self._countrate is None:
            #self._countrate = np.average(self._trace[:,1])
            # Take into account traces that have arbitrary sampling
            self._countrate = spintg.simps(self._trace[:,1], self._trace[:,0]) / self.duration
        return self._countrate
    
    @countrate.setter
    def countrate(self, value):
        assert value is not None, "Setting value with None forbidden!"
        assert self._trace is None, "Setting value impossible, "+\
                                    "if `self.trace` is set."
        self._countrate = value

    @property
    def duration(self):
        if not hasattr(self, "_duration") or self._duration is None:
            self._duration = self._trace[-1,0] - self._trace[0,0]
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
        # self.countrate is set automagically


class Correlation(object):
    """ unifies correlation curve handling
    """
    def __init__(self, backgrounds=[], correlation=None, corr_type="AC", 
                 filename=None, fit_algorithm="Lev-Mar",
                 fit_model=6000, fit_ival=(0,0),
                 fit_weight_data=None, fit_weight_type="none", 
                 normparm=None, title=None, traces=[], verbose=1):
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
        fit_ival:
            fitting interval of lag times in indices
        fit_model: instance of FitModel
            the model used for fitting
        fit_weight_data: any
            data for the certain fit_weight_type
        fit_weight_type: str
            Reserved keywords or user-defined strings:
             - "none" : no weights are used
             - "splineX" : compute weights from spline with X knots
                   and a spread of `fit_weight_data` bins.
             - "model function" : compute weights from difference
                   to model function
             - user-defined : other weights (e.g. previously computed 
                   averages given in fit_weight_data)
        normparm: int
            identifier of normalization parameter
        title: str
            user-editable title of this correlation
        traces: list of instances of Trace
            traces of the current correlation
        verbose : int
            increment to increase verbosity
        """
        # must be created before setting properties
        self._backgrounds = []
        self._correlation = None
        self._fit_algorithm = None   
        self._fit_model = None
        self._fit_parameters = None
        self._fit_parameters_range = None
        self._fit_parameters_variable = None
        self._fit_weight_memory = dict()
        self._lag_time = None
        self._model_memory = dict()
        self._traces = []
        self._uid = None

        self.verbose = verbose

        self.backgrounds = backgrounds
        self.bg_correction_enabled = True
        self.correlation = correlation
        self.corr_type = corr_type
        self.filename = filename
        
        self.fit_algorithm = fit_algorithm
        self.fit_ival = fit_ival
        self.fit_model = fit_model
        # Do not change order:
        self.fit_weight_type = fit_weight_type
        self.fit_weight_parameters = fit_weight_data
    
        self.normparm = normparm
        self.title = title
        self.traces = traces

    def __repr__(self):
        if self.is_ac:
            c = "AC"
        else:
            c = "CC"
        text = "{} correlation '{}' with {} traces".format(
                c, self.title, len(self._traces))
        return text


    def background_replace(self, channel, background):
        """
        Replace a background.
        Channel must be 0 or 1.
        background must be instance of `Trace`
        """
        assert channel in [0, 1]
        assert isinstance(background, Trace)
        
        if self.is_ac:
            if channel == 1:
                raise ValueError("Cannot set second background for AC.")
            self._backgrounds = [background]
        else:
            if len(self._backgrounds) == 0:
                self._backgrounds = [Trace(countrate=0, duration=0), Trace(countrate=0, duration=0)]
            elif len(self._backgrounds) == 1:
                self._backgrounds.append(Trace(countrate=0, duration=0))
            self._backgrounds[channel] = background

    @property
    def backgrounds(self):
        """
        The background trace(s) of this correlation in a list.
        """
        return self._backgrounds
    
    @backgrounds.setter
    def backgrounds(self, value):
        """
        Set the backgrounds. The value can either be a list of traces or
        instances of traces or a single trace in an array.
        """
        backgrounds = []
        if not isinstance(value, list):
            value = [value]
        assert len(value) in [0,1,2], "Backgrounds must be list with up to two elements."
        for v in value:
            if isinstance(v, np.ndarray):
                backgrounds.append(Trace(trace=v))
            elif isinstance(v, Trace):
                backgrounds.append(v)
            else:
                raise ValueError("Each background must be instance of Trace or ndarray")
        self._backgrounds = backgrounds


    @property
    def bg_correction_factor(self):
        """
        Returns background correction factor for
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
                if self.verbose >= 1:
                    warnings.warn("Correlation {}: no bg-correction".
                                  format(self.uid))
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
                              format(self))
                bgfactor = 1
        return bgfactor

    def check_parms(self, parms):
        """ Check parameters using self.fit_model.func_verification and the user defined
            boundaries self.fit_parameters_range for each parameter.
        """
        p = 1.*np.array(parms)
        r = self.fit_parameters_range
        for i in range(len(p)):
            if r[i][0] == r[i][1]:
                pass
            elif r[i][0] is None:
                if p[i] > r[i][1]:
                    p[i] = r[i][1]
            elif r[i][1] is None:
                if p[i] < r[i][0]:
                    p[i] = r[i][1]
            elif p[i] < r[i][0]:
                p[i] = r[i][0]
            elif p[i] > r[i][1]:
                p[i] = r[i][1]
        return p

    @property
    def correlation(self):
        """the correlation data, shape (N,2) with (time, correlation) """
        if self._correlation is not None:
            corr = self._correlation.copy()
            return corr
    
    @correlation.setter
    def correlation(self, value):
        if value is None:
            warnings.warn("Setting correlation to `None`.")
        elif not isinstance(value, np.ndarray):
            raise ValueError("Correlation must be 2d array!")
        elif not value.shape[1] == 2:
            raise ValueError("Correlation array must have shape (N,2)!")
        self._correlation = value

    @property
    def correlation_fit(self):
        """ returns correlation data for fitting (fit_ivald)
        - background correction
        - fitting interval cropping
        """
        corr = self.correlation
        if corr is not None:
            # perform background correction
            corr[:,1] *= self.bg_correction_factor
            # perform parameter normalization
            return corr[self.fit_ival[0]:self.fit_ival[1],:]
        
    
    @property
    def correlation_plot(self):
        """ returns correlation data for plotting (normalized, fit_ivald)
        - background correction
        - fitting interval cropping
        - parameter normalization
        """
        corr = self.correlation_fit
        if corr is not None:
            # perform parameter normalization
            corr[:,1] *= self.normalize_factor
            return corr

    @property
    def is_ac(self):
        """True if instance contains autocorrelation"""
        return self.corr_type.lower().count("ac") > 0

    @property
    def is_cc(self):
        """True if instance contains crosscorrelation"""
        return not self.is_ac

    @property
    def is_weighted_fit(self):
        """True if a weighted fit was performed"""
        return self.fit_weight_type != "none"

    @property
    def fit_algorithm(self):
        """The string representing the fitting algorithm"""
        return self._fit_algorithm

    @fit_algorithm.setter
    def fit_algorithm(self, value):
        # TODO:
        # - allow lower-case fitting algorithm
        assert value in list(Algorithms.keys()), "Invalid fit algorithm: "+value
        self._fit_algorithm = value

    @property
    def fit_model(self):
        """instance of a fit model"""
        return self._fit_model

    @fit_model.setter
    def fit_model(self, value):
        """set the fit model
        """
        if isinstance(value, (int, long)):
            newmodel = mdls.modeldict[value]
        elif isinstance(value, mdls.Model):
            newmodel = value
        else:
            raise NotImplementedError("Unknown model identifier")
        
        if newmodel != self._fit_model :
            self._fit_model = newmodel
            # overwrite fitting parameters
            self._fit_parameters = self._fit_model.default_values
            self._fit_parameters_variables = self._fit_model.default_variables
            self._fit_parameters_range = np.zeros((len(self._fit_parameters), 2))
            self.normalize_parm = None

    @property
    def fit_ival(self):
        """lag time interval for fitting"""
        lag = self.lag_time
        if lag is not None:
            if self._fit_ival[1] <= 0 or self._fit_ival[1] > lag.shape[0]:
                self._fit_ival[1] = lag.shape[0]
        return self._fit_ival
    
    @fit_ival.setter
    def fit_ival(self, value):
        value = list(value)
        if value[1] <= 0:
            if self.lag_time is not None:
                value[1] = self.lag_time.shape[0]
            else:
                # just to be sure
                warnings.warn("No data available.")
                value[1] = 10000000000000000
        self._fit_ival = value

    @property
    def fit_weight_data(self):
        """data of weighted fitting"""
        try:
            data = self._fit_weight_memory[self.fit_weight_type]
        except KeyError:
            # Standard variables for weights
            if self.fit_weight_type.count("spline"):
                # Default area for weighting with spline fit
                data = 3
            else:
                data = None
        return data

    @fit_weight_data.setter
    def fit_weight_data(self, value):
        self._fit_weight_memory[self.fit_weight_type] = value

    @property
    def fit_parameters(self):
        """parameters that were fitted/will be used for fitting"""
        # Do not return `self._fit_parameters.copy()`, because
        # some methods of PyCorrFit depende on the array being
        # accessible and changeable with indices.
        return self._fit_parameters

    @fit_parameters.setter
    def fit_parameters(self, value):
        # must unlock parameters, if change is required
        value = np.array(value)
        self._fit_parameters = self.check_parms(value)

    @property
    def fit_parameters_range(self):
        """valid fitting ranges for fit parameters"""
        model = self.fit_model.boundaries
        mine = self._fit_parameters_range
        new = []
        for a, b in zip(model, mine):
            c = [-np.inf, np.inf]
            if a[0] != a[1]:
                c[0] = a[0]
                c[1] = a[1]
            # user overrides model
            if b[0] != b[1]:
                c[0] = b[0]
                c[1] = b[1]
            if c[0] is not None and np.isnan(c[0]):
                c[0] = -np.inf
            if c[1] is not None and np.isnan(c[1]):
                c[1] = np.inf

            new.append(c)         
        return np.array(new)

    @fit_parameters_range.setter
    def fit_parameters_range(self, value):
        value = np.array(value)
        assert value.shape[1] == 2
        assert value.shape[0] == self.fit_parameters.shape[0]
        self._fit_parameters_range = value

    @property
    def fit_parameters_variable(self):
        """which parameters are variable during fitting"""
        if self._fit_parameters_variable is None:
            self._fit_parameters_variable = np.array(self.fit_model.default_variables, dtype=bool)
        return self._fit_parameters_variable

    @fit_parameters_variable.setter
    def fit_parameters_variable(self, value):
        value = np.array(value, dtype=bool)
        assert value.shape[0] == self.fit_parameters.shape[0]
        self._fit_parameters_variable = value

    @property
    def lag_time(self):
        """logarithmic lag time axis"""
        if self.correlation is not None:
            return self._correlation[:,0].copy()
        elif self._lag_time is not None:
            return self._lag_time
        else:
            # some default lag time
            return 10**np.linspace(-6,8,1001)

    @lag_time.setter
    def lag_time(self, value):
        if self.correlation is not None:
            warnings.warn("Setting lag time not possible, because of existing correlation")
        else:
            self._lag_time = value

    @property
    def lag_time_fit(self):
        """lag time as used for fitting"""
        return self.lag_time[self.fit_ival[0]:self.fit_ival[1]]

    @property
    def modeled(self):
        """fitted data values, same shape as self.correlation"""
        # perform parameter normalization
        lag = self.lag_time
        modeled = np.zeros((lag.shape[0], 2))
        modeled[:,0] = lag
        modeled[:,1] = self.fit_model(self.fit_parameters, lag)
        return modeled.copy()

    @property
    def modeled_fit(self):
        """fitted data values, same shape as self.correlation_fit"""
        toplot = self.modeled[self.fit_ival[0]:self.fit_ival[1], :]
        return toplot

    @property
    def modeled_plot(self):
        """fitted data values, same shape as self.correlation_fit"""
        toplot = self.modeled_fit
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
            nfactor = alt[self.normparm - self.fit_parameters.shape[0]]
        
        return nfactor

    @property
    def residuals(self):
        """fit residuals, same shape as self.correlation"""
        if self.correlation is None:
            raise ValueError("Cannot compute residuals; No correlation given!") 
        residuals = self.correlation.copy()
        residuals[:,1] -= self.modeled[:,1]
        return residuals 
    
    @property
    def residuals_fit(self):
        """fit residuals, same shape as self.correlation_fit"""
        residuals_fit = self.correlation_fit.copy()
        residuals_fit[:,1] -= self.modeled_fit[:,1]
        return residuals_fit

    @property
    def residuals_plot(self):
        """fit residuals, same shape as self.correlation_fit"""
        cp = self.correlation_plot
        if cp is not None:
            residuals_plot = self.correlation_plot.copy()
            residuals_plot[:,1] -= self.modeled_plot[:,1]
            return residuals_plot

    def set_weights(self, type_name, data):
        """
        Add weights for fitting.
        example:
        type_name : "Average"
        data : 1d ndarray with length self.lag_time 
        """
        if data is not None:
            self._fit_weight_memory[type_name] = data

    @property
    def traces(self):
        """
        The trace(s) of this correlation in a list.
        """
        return self._traces
    
    @traces.setter
    def traces(self, value):
        """
        Set the traces. The value can either be a list of traces or
        instances of traces or a single trace in an array.
        """
        traces = []
        if not isinstance(value, list):
            value = [value]
        assert len(value) in [0,1,2], "Traces must be list with up to two elements."
        for v in value:
            if isinstance(v, np.ndarray):
                traces.append(Trace(trace=v))
            elif isinstance(v, Trace):
                traces.append(v)
            else:
                raise ValueError("Each trace must be instance of Trace or ndarray")
        self._traces = traces
        
        if len(self._traces) == 2:
            if self._traces[0].duration != self._traces[1].duration:
                warnings.warn("Unequal lenght of traces: {} and {}".format(
                              self._traces[0].duration,
                              self._traces[1].duration))

    @property
    def uid(self):
        """
        unique identifier of this instance
        This might change when title or filename
        are updated.
        """
        if self._uid is None:
            hasher = hashlib.sha256()
            hasher.update(str(np.random.random()))
            hasher.update(str(self._correlation))
            hasher.update(str(self.filename))
            hasher.update(str(self.title))
            self._uid = hasher.hexdigest()
        return self._uid


class Fit(object):
    """ Used for fitting FCS data to models.
    """
    def __init__(self, correlations=[], global_fit=False,
                 global_fit_variables=[],
                 uselatex=False, verbose=0):
        """ Using an FCS model, fit the data of shape (N,2).


        Parameters
        ----------
        correlations: list of instances of Correlation
            Correlations to fit.
        global fit : bool
            Perform global fit. The default behavior is
            to fit all parameters that are selected for
            fitting in each correlation. Parameters with
            the same name in different models are treated
            as one global parameter. 
        global_fit_variables: list of list of strings
            Each item contains a list of strings that are names
            of parameters which will be treated as a common
            parameter. This breaks the defaul behavior.
            NOT IMPLEMENTED YET!
        verbose: int
            Increase verbosity by incrementing this number.
        uselatex: bool
            If verbose > 0, plotting will be performed with LaTeX.
        """
        assert len(global_fit_variables)==0, "not implemented"
        
        if isinstance(correlations, Correlation):
            correlations = [correlations]
        
        self.correlations = correlations
        self.global_fit_variables = global_fit_variables
        self.verbose = verbose
        self.uselatex = uselatex
        self.is_weighted_fit = False
        
        if not global_fit:
            # Fit each correlation separately
            for corr in self.correlations:
                # Set fitting options
                self.fit_algorithm = corr.fit_algorithm
                # Get the data required for fitting
                self.x = corr.correlation_fit[:,0]
                self.y = corr.correlation_fit[:,1]
                # fit_bool: True for variable
                self.fit_bool = corr.fit_parameters_variable.copy()
                self.fit_parm = corr.fit_parameters.copy()
                self.fit_bound = copy.copy(corr.fit_parameters_range)
                self.is_weighted_fit = corr.is_weighted_fit
                self.fit_weights = Fit.compute_weights(corr,
                                                   verbose=verbose,
                                                   uselatex=uselatex)
                self.fit_parm_names = corr.fit_model.parameters[0]
                self.func = corr.fit_model.function
                self.check_parms = corr.check_parms
                self.constraints = corr.fit_model.constraints
                # Directly perform the fit and set the "fit" attribute
                self.minimize()
                # Run a second time:
                self.minimize()
                # update correlation model parameters
                corr.fit_parameters = self.fit_parm
                # save fit instance in correlation class
                corr.fit_results = self.get_fit_results(corr)
        else:
            # TODO:
            # - allow detaching of parameters,
            #   i.e. fitting "n" separately for two models
            # Initiate all arrays
            self.fit_algorithm = self.correlations[0].fit_algorithm
            xtemp = []      # x
            ytemp = []      # y
            weights = []    # weights
            ids = [0]           # ids in big fitting array
            cmodels = []    # correlation model info
            initpar = []    # initial parameters
            varin = []      # names of variable fitting parameters
            variv = []      # values of variable fitting parameters
            varmap = []     # list of indices of fitted parameters
            varbound = []   # list of fitting boundaries
            self.is_weighted_fit = None
            for corr in self.correlations:
                xtemp.append(corr.correlation_fit[:,0])
                ytemp.append(corr.correlation_fit[:,1])
                weights.append(Fit.compute_weights(corr))
                ids.append(len(xtemp[-1])+ids[-1])
                cmodels.append(corr.fit_model)
                initpar.append(corr.fit_parameters)
                # Create list of variable parameters
                varthis = []
                for ipm, par in enumerate(corr.fit_model.parameters[0]):
                    if corr.fit_parameters_variable[ipm]:
                        varthis.append(ipm)
                        varin.append(par)
                        variv.append(corr.fit_parameters[ipm])
                        varbound.append(corr.fit_parameters_range[ipm])
                varmap.append(varthis)

            # These are the variable fitting parameters
            __, varidx = np.unique(varin, return_index=True)
            varidx.sort()
            varin = np.array(varin)[varidx]
            variv = np.array(variv)[varidx]
            
            self.x = np.concatenate(xtemp)
            self.y = np.concatenate(ytemp)
            self.fit_bool = np.ones(len(variv), dtype=bool)
            self.fit_parm = variv
            self.fit_weights = np.concatenate(weights)
            self.fit_parm_names = varin
            self.fit_bound = varbound
            self.constraints = []
            warnings.warn("Constraints are not supported yet for global fitting.")
            
            
            def parameters_global_to_local(parameters, iicorr, varin=varin,
                                          initpar=initpar,
                                          correlations=correlations):
                """
                With global `parameters` and an id `iicorr` pointing at
                the correlation in `self.correlations`, return the
                updated parameters of the corresponding model.
                """
                fit_parm = initpar[iicorr].copy()
                corr = correlations[iicorr]
                mod = corr.fit_model
                for kk, pn in enumerate(mod.parameters[0]):
                    if pn in varin:
                        # edit that parameter
                        fit_parm[kk] = parameters[np.where(np.array(varin)==pn)[0]]
                return fit_parm
            
            def parameters_local_to_global(parameters, iicorr, fit_parm,
                                           varin=varin,
                                           correlations=correlations):
                """
                inverse of parameters_global_to_local
                """
                corr = correlations[iicorr]
                mod = corr.fit_model
                for kk, pn in enumerate(mod.parameters[0]):
                    if pn in varin:
                        # edit that parameter
                        parameters[np.where(np.array(varin)==pn)[0]] = fit_parm[kk]
                return parameters
            
            # Create function for fitting using ids
            def global_func(parameters, tau,
                            glob2loc=parameters_global_to_local):
                out = []
                # ids start at 0
                for ii, mod in enumerate(cmodels):
                    # Update parameters
                    fit_parm = glob2loc(parameters, ii)
                    # return function
                    out.append(mod.function(fit_parm, tau[ids[ii]:ids[ii+1]]))
                return np.concatenate(out)

            self.func = global_func
            
            # Create function for checking
            def global_check_parms(parameters,
                                   glob2loc=parameters_global_to_local,
                                   loc2glob=parameters_local_to_global):

                for ii, corr in enumerate(self.correlations):
                    # create new initpar
                    fit_parm = glob2loc(parameters, ii)
                    fit_parm = corr.check_parms(fit_parm)
                    # update parameters
                    parameters = loc2glob(parameters, ii, fit_parm)

                return parameters
            
            self.check_parms = global_check_parms

            # Directly perform the fit and set the "fit" attribute
            self.minimize()
            # Update correlations
            for ii, corr in enumerate(self.correlations):
                # write new model parameters
                corr.fit_parameters = parameters_global_to_local(self.fit_parm,
                                                                 ii)
                # save fit instance in correlation class
                corr.fit_results = self.get_fit_results(corr)


    def get_fit_results(self, correlation):
        """
        Return a dictionary with all information about the performed fit.
        
        This function must be called immediately after `self.minimize`.
        """
        c = correlation
        d = {
             "chi2" : self.chi_squared,
             "chi2 type" : self.chi_squared_type,
             "weighted fit" : c.is_weighted_fit,
             "fit algorithm" : c.fit_algorithm,
             "fit result" : c.fit_parameters.copy(),
             "fit parameters" : np.where(c.fit_parameters_variable)[0],
             "fit weights" : self.compute_weights(c)
             }
        
        
        if c.is_weighted_fit:
            d["weighted fit type"] = c.fit_weight_type
            if isinstance(c.fit_weight_data, (int, float)):
                d["weighted fit bins"] = c.fit_weight_data

        if d["fit algorithm"] == "Lev-Mar" and self.parmoptim_error is not None:
            d["fit error estimation"] = self.parmoptim_error
        
        
        return d
        

    @property
    def chi_squared(self):
        """ Calculate displayed Chi²
        
            Calculate reduced Chi² for the current class.
        """
        # Calculate degrees of freedom
        dof = len(self.x) - np.sum(self.fit_bool) - 1
        # This is exactly what is minimized by the scalar minimizers
        
        if self.chi_squared_type == "reduced expected sum of squares":
            fitted = self.func(self.fit_parm, self.x)
            chi2 = np.sum((self.y-fitted)**2/np.abs(fitted)) / dof
        elif self.chi_squared_type == "reduced weighted sum of squares":
            fitted = self.func(self.fit_parm, self.x)
            variance = self.fit_weights**2
            chi2 = np.sum((self.y-fitted)**2/variance) / dof
        elif self.chi_squared_type == "reduced global sum of squares":
            fitted = self.func(self.fit_parm, self.x)
            variance = self.fit_weights**2
            chi2 = np.sum((self.y-fitted)**2/variance) / dof
        else:
            chi2 = self.fit_function_scalar(self.fit_parm, self.x, self.y, self.fit_weights)
        
            
        return chi2


    @property
    def chi_squared_type(self):
        """ The type of Chi² that currently applies.
        
        Returns
        -------
        "reduced" - if variance of data was used for fitting
        "reduced Pearson" - if variance of data is not available
        """
        if self.is_weighted_fit is None:
            # global fitting
            return "reduced global sum of squares"
        elif self.is_weighted_fit == True:
            return "reduced weighted sum of squares"
        elif self.is_weighted_fit == False:
            return "reduced expected sum of squares"
        else:
            raise ValueError("Unknown weight type!")


    @staticmethod
    def compute_weights(correlation, verbose=0, uselatex=False):
        """ computes and returns weights of the same length as 
        `correlation.correlation_fit`
        
        `correlation` is an instance of Correlation
        """
        corr = correlation
        model = corr.fit_model
        model_parms = corr.fit_parameters
        ival = corr.fit_ival
        weight_data = corr.fit_weight_data
        weight_type = corr.fit_weight_type
        #parameters = corr.fit_parameters
        #parameters_range = corr.fit_parameters_range
        #parameters_variable = corr.fit_parameters_variable
        
        cdat = corr.correlation
        if cdat is None:
            raise ValueError("Cannot compute weights; No correlation given!")
        cdatfit = corr.correlation_fit
        x_full = cdat[:,0]
        y_full = cdat[:,1]
        x_fit = cdatfit[:,0]
        #y_fit = cdatfit[:,1]
        
        dataweights = np.ones_like(x_fit)

        try:
            weight_spread = int(weight_data)
        except:
            if verbose > 1:
                warnings.warn("Could not get weight spread for spline. Setting it to 3.")
            weight_spread = 3

        if weight_type[:6] == "spline":
            # Number of knots to use for spline
            try:
                knotnumber = int(weight_type[6:])
            except:
                if verbose > 1:
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
            if x_full.shape[0] - ival[1] < weight_spread:
                # optimal case
                pmax = x_full.shape[0] - ival[1]
            else:
                # non-optimal case
                # we need to cut pmax
                pmax = weight_spread

            x = x_full[ival[0]-pmin:ival[1]+pmax]
            y = y_full[ival[0]-pmin:ival[1]+pmax]
            # we are fitting knots on a base 10 logarithmic scale.
            xs = np.log10(x)
            knots = np.linspace(xs[1], xs[-1], knotnumber+2)[1:-1]
            try:
                tck = spintp.splrep(xs, y, s=0, k=3, t=knots, task=-1)
                ys = spintp.splev(xs, tck, der=0)
            except:
                if verbose > 0:
                    raise ValueError("Could not find spline fit with "+\
                                     "{} knots.".format(knotnumber))
                return
            if verbose > 0:
                ## If plotting module is available:
                #name = "spline fit: "+str(knotnumber)+" knots"
                #plotting.savePlotSingle(name, 1*x, 1*y, 1*ys,
                #                         dirname=".",
                #                         uselatex=uselatex)
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
            # to ival[1] is chosen, such that the dataweights must be
            # calculated from unknown datapoints.
            # (e.g. points+endcrop > len(correlation)
            # We deal with this by multiplying dataweights with a factor
            # corresponding to the missed points.
            for i in range(x_fit.shape[0]):
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
                # i: counter on correlation array
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
            # Number of neighboring (left and right) points to include
            if ival[0] < weight_spread:
                pmin = ival[0]
            else:
                pmin = weight_spread
            if x_full.shape[0] - ival[1] <  weight_spread:
                pmax = x_full.shape[0] - ival[1]
            else:
                pmax = weight_spread
            x = x_full[ival[0]-pmin:ival[1]+pmax]
            y = y_full[ival[0]-pmin:ival[1]+pmax]
            # Calculated dataweights
            for i in np.arange(x_fit.shape[0]):
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
                # i: counter on correlation array
                # start: counter on correlation array
                start = i - weight_spread + offsetstart + ival[0] - offsetcrop
                end = start + 2*weight_spread + 1 - offsetstart
                #start = ival[0] - weight_spread + i
                #end = ival[0] + weight_spread + i + 1
                diff = y - model(model_parms, x)
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
        elif weight_type == "none":
            pass
        else:
            # This means that the user knows the dataweights and already
            # gave it to us.
            weights = weight_data
            assert weights is not None, "User defined weights not given: "+weight_type
            
            # Check if these other weights have length of the cropped
            # or the full array.
            if weights.shape[0] == x_fit.shape[0]:
                dataweights = weights
            elif weights.shape[0] == x_full.shape[0]:
                dataweights = weights[ival[0]:ival[1]]
            else:
                raise ValueError, \
                  "`weights` must have length of full or cropped array."
        
        return dataweights
        

    def fit_function(self, params, x, y, weights=1):
        """ 
        objective function that returns the residual (difference between
        model and data) to be minimized in a least squares sense.
        """
        parms = Fit.lmfitparm2array(params)
        tominimize = (self.func(parms, x) - y)
        # Check dataweights for zeros and don't use these
        # values for the least squares method.
        with np.errstate(divide='ignore'):
            tominimize = np.where(weights!=0, 
                                  tominimize/weights, 0)
        ## There might be NaN values because of zero weights:
        #tominimize = tominimize[~np.isinf(tominimize)]
        return tominimize

    def fit_function_scalar(self, parms, x, y, weights=1):
        """
        Wrapper of `fit_function`.
        Returns the sum of squares of the input data.
        """
        e = self.fit_function(parms, x, y, weights)
        return np.sum(e*e)

    def get_lmfitparm(self):
        """
        Generates an lmfit parameter class from the present data set.

        The following parameters are used:
        self.x : 1d ndarray length N
        self.y : 1d ndarray length N
        self.fit_weights : 1d ndarray length N
        
        self.fit_bool : 1d ndarray length P, bool
        self.fit_parm : 1d ndarray length P, float
        """
        params = lmfit.Parameters()

        # First, add all fixed parameters
        for pp in range(len(self.fit_parm)):
            if not self.fit_bool[pp]:
                if self.fit_bound[pp][0] == self.fit_bound[pp][1]:
                    self.fit_bound[pp]=[-np.inf, np.inf]
                params.add(lmfit.Parameter(name="parm{:04d}".format(pp),
                                           value=self.fit_parm[pp],
                                           vary=self.fit_bool[pp],
                                           min=self.fit_bound[pp][0],
                                           max=self.fit_bound[pp][1],
                                            )
                                           )
        
        # Second, summarize the constraints in a dictionary, where
        # keys are the parameter indexes of varied parameters.
        # The dictionary cstrnew only allows integer keys that are
        # representing parameter indices. The fact that we are effectively
        # reducing the number of valid constraints to one per parameter
        # is a design problem that cannot be resolved here. The constraints
        # must be defined in such a way, that a parameter with a larger
        # index number is dependent on only one parameter with a lower
        # index number, e.g. parm1>parm0, parm3<parm1, etc..
        cstrnew = {}
        bound = np.array(self.fit_bound).copy()
        for cc in self.constraints:
            if self.fit_bool[cc[0]] and self.fit_bool[cc[2]]:
                # Both cc[0] and c[2] are varied.
                # Everything will work fine, independent of the
                # the fact if cc[2] is varied or not.
                cstrnew[cc[0]] = [cc[1], cc[2]]
            elif self.fit_bool[cc[0]]:
                # Only cc[0] is varied, create boundary
                if cc[1] == "<":
                    # maximum
                    bnd = [-np.inf, self.fit_parm[cc[2]]]
                elif cc[1] == ">":
                    # minimum
                    bnd = [self.fit_parm[cc[2]], np.inf]
                # update boundaries if necessary
                bound[cc[0]] = [max(bound[cc[0]][0], bnd[0]),
                                min(bound[cc[0]][1], bnd[1])]
            elif self.fit_bool[cc[2]]:
                # Only cc[2] is varied, create boundary
                if cc[1] == "<":
                    # minimum boundary
                    bnd = [self.fit_parm[cc[0]], np.inf]
                elif cc[1] == ">":
                    # maximum boundary
                    bnd = [-np.inf, self.fit_parm[cc[0]]]
                # update boundaries if necessary
                bound[cc[2]] = [max(bound[cc[2]][0], bnd[0]),
                                min(bound[cc[2]][1], bnd[1])]
            else:
                # Neither cc[0] nor cc[2] are varied.
                # Do nothing.
                pass

        # Third, setup all variable parameters with the necessary constraints.
        for pp in range(len(self.fit_parm)):
            if self.fit_bool[pp]:
                # analyze constraints using lmfit:
                if pp in cstrnew:
                    # constrained parameters
                    ppref = cstrnew[pp][1]
                    rel = cstrnew[pp][0]
                    #TODO:
                    # - combine the two following cases for better readybility
                    if rel == "<":
                        #p2 < p1
                        #-> p2 = p1 - d21
                        #-> d21 = p1 - p2
                        #-> d21 > 0
                        deltaname="delta_{}_{}".format(pp, ppref)
                        params.add(lmfit.Parameter(name=deltaname,
                                               value=self.fit_parm[ppref]-self.fit_parm[pp],
                                               vary=self.fit_bool[pp],
                                               min=0,
                                               max=np.inf,
                                                ))
                        ppcomp = "parm{:04d}-{}".format(ppref, deltaname)
                        params.add(lmfit.Parameter(name="parm{:04d}".format(pp),
                                                         # this condition deals with negative numbers
                                                   expr="{MIN} if {COMP} < {MIN} else {MAX} if {COMP} > {MAX} else {COMP}".format(
                                                        COMP=ppcomp,
                                                        MIN=bound[pp][0],
                                                        MAX=bound[pp][1])
                                                ))
                    elif rel == ">":
                        # The opposite of the above case
                        #p2 > p1
                        #-> p2 = p1 + d21
                        #-> d21 = p2 - p1
                        #-> d21 > 0
                        deltaname="delta_{}_{}".format(pp, ppref)
                        params.add(lmfit.Parameter(name=deltaname,
                                               value=self.fit_parm[pp]-self.fit_parm[ppref],
                                               vary=self.fit_bool[pp],
                                               min=0,
                                               max=np.inf,
                                                ))
                        ppcomp = "parm{:04d}+{}".format(ppref, deltaname)
                        params.add(lmfit.Parameter(name="parm{:04d}".format(pp),
                                                         # this condition deals with negative numbers
                                                   expr="{MIN} if {COMP} < {MIN} else {MAX} if {COMP} > {MAX} else {COMP}".format(
                                                        COMP=ppcomp,
                                                        MIN=bound[pp][0],
                                                        MAX=bound[pp][1])
                                                ))
                    else:
                        raise NotImplementedError("Only '<' and '>' are allowed constraints!")
                
                else:
                    ## normal parameter
                    params.add(lmfit.Parameter(name="parm{:04d}".format(pp),
                                               value=self.fit_parm[pp],
                                               vary=self.fit_bool[pp],
                                               min=bound[pp][0],
                                               max=bound[pp][1],
                                                )
                                               )
        return params

    @staticmethod
    def lmfitparm2array(parms, parmid="parm", attribute="value"):
        """
        Convert lmfit parameters to a numpy array.
        Parameters are identified by name `parmid` which should
        be at the beginning of a parameters.
        
        This method is necessary to separate artificial constraint parameters
        from the actual parameters.
        
        Parameters
        ----------
        parms : lmfit.parameter.Parameters or ndarray
            The input parameters.
        parmid : str
            The identifier for parameters. By default this is
            "parm", i.e. parameters are named like this:
            "parm0001", "parm0002", etc.
        attribute : str
            The attribute to return, e.g.
            - "value" : return the current value of the parameter
            - "vary" : return if the parameter is varied during fitting
        
        Returns:
        parr : ndarray
            If the input is an ndarray, the input will be returned.
        """
        if isinstance(parms, lmfit.parameter.Parameters):
            items = parms.items()
            items.sort(key=lambda x: x[0])
            parr = [getattr(p[1], attribute) for p in items if p[0].startswith(parmid)]
        else:
            parr = parms

        return np.array(parr)

    def minimize(self):
        """ This will run the minimization process
      
        """
        assert (np.sum(self.fit_bool) != 0), "No parameter selected for fitting."
        
        # get all parameters for minimization
        params = self.get_lmfitparm()
        
        # Get algorithm
        method = Algorithms[self.fit_algorithm][0]
        methodkwargs = Algorithms[self.fit_algorithm][2]

        # Begin fitting
        # Fit a several times and stop earlier if the residuals
        # are small enough (heuristic approach).
        nfits = 5
        diff = np.inf
        parmsinit = Fit.lmfitparm2array(params)
        for ii in range(nfits):
            res0 = self.fit_function(params, self.x, self.y)
            result = lmfit.minimize(fcn=self.fit_function,
                                    params=params,
                                    method=method,
                                    kws={"x":self.x,
                                            "y":self.y,
                                            "weights":self.fit_weights},
                                    **methodkwargs
                                    )
            params = result.params
            res1 = self.fit_function(params, self.x, self.y)
            diff = np.average(np.abs(res0-res1))

            if hasattr(result, "ier") and not result.errorbars and ii+1 < nfits:
                # This case applies to the Levenberg-Marquardt algorithm
                multby = .5
                # Try to vary stuck fitting parameters
                # the result from the previous fit
                parmsres = Fit.lmfitparm2array(params)
                # the parameters that are varied during fitting
                parmsbool = Fit.lmfitparm2array(params, attribute="vary")
                # The parameters that are stuck
                parmstuck = parmsbool * (parmsinit==parmsres)
                parmsres[parmstuck] *= multby
                # write changes
                self.fit_parm = parmsres
                params = self.get_lmfitparm()
                warnings.warn(u"PyCorrFit detected problems in fitting, "+\
                              u"detected a stuck parameter, multiplied "+\
                              u"it by {}, and fitted again. ".format(multby)+\
                              u"The stuck parameters are: {}".format(
                                np.array(self.fit_parm_names)[parmstuck]))
            elif diff < 1e-8:
                # Experience tells us this is good enough.
                break

        # Now write the optimal parameters to our values:
        self.fit_parm = Fit.lmfitparm2array(params)
        # Only allow physically correct parameters
        self.fit_parm = self.check_parms(self.fit_parm)
        # Compute error estimates for fit (Only "Lev-Mar")
        if self.fit_algorithm == "Lev-Mar" and result.success:
            # This is the standard way to minimize the data. Therefore,
            # we are a little bit more verbose.
            self.covar = result.covar
            try:
                self.parmoptim_error = np.diag(self.covar)
            except:
                warnings.warn("PyCorrFit Warning: Error estimate not "+\
                              "possible, because we could not "+\
                              "calculate covariance matrix. Please "+\
                              "try reducing the number of fitting "+\
                              "parameters.")
                self.parmoptim_error = None
        else:
            self.parmoptim_error = None



def GetAlgorithmStringList():
    """
        Get supported fitting algorithms as strings.
        Returns two lists (that are key-sorted) for key and string.
    """
    A = Algorithms
    out1 = []
    out2 = []
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
Algorithms["Lev-Mar"] = ["leastsq", 
                         "Levenberg-Marquardt",
                         {"ftol" : 1.49012e-08,
                          "xtol" : 1.49012e-08,
                          }
                        ]

# simplex 
Algorithms["Nelder-Mead"] = ["nelder",
                             "Nelder-Mead (downhill simplex)",
                             {}
                             ]

# quasi-Newton method of Broyden, Fletcher, Goldfarb, and Shanno
Algorithms["BFGS"] = ["lbfgsb",
                      "BFGS (quasi-Newton)",
                      {}
                      ]

# modified Powell-method
Algorithms["Powell"] = ["powell",
                        "modified Powell (conjugate direction)",
                        {}
                        ]

# nonliner conjugate gradient method by Polak and Ribiere
Algorithms["SLSQP"] = ["slsqp",
                       "Sequential Linear Squares Programming",
                       {}
                       ]
