# -*- coding: utf-8 -*-
""" PyCorrFit data set

Classes for FCS data evaluation.
"""
from __future__ import print_function, division

import copy
import lmfit
import numpy as np
import scipy.interpolate as spintp
import warnings


class Constraint(object):
    """ Class to translate fit constraints to lmfit syntax.
    """
    def __init__(self, constraint, fit_bool, fit_bounds, fit_values):
        """
        Parameters
        ----------
        constraint : list of strings and ints
            The abstract constraint (e.g. [1, 0, "<", "2.3"]) as
            used in the model definitions.
        fit_bool : list of boolean
            A list of bools indicating which parameters are varied
            during fitting.
        fit_bounds : list of lists of two floats
            The parameter boundaries for fitting.
        fit_values : list of floats
            The initial fitting values.
        
        Notes
        -----
        - the first item in constraints must be an integer indexing a parameter
        - the second/third item must be an integer as well or an operator (">", "<")
        - if the fourth item is omitted, it is assumed to be "0"
        - the first integer must be larger than the second integer
        """
        if len(constraint) == 3:
            constraint.append("0")
            
        self.constraint = constraint
        self.fit_bool = fit_bool
        self.fit_bounds = fit_bounds
        self.fit_values = fit_values
    
    @property
    def parameters(self):
        """
        Returns list of dict for each parameter.
        """
        parms = [ it for it in self.constraint if isinstance(it, (int, long))]
        id2 = self.constraint.index(parms[1])
        
        p1 = {"id": parms[0],
              "bool": self.fit_bool[parms[0]],
              "sign": +1,
              "value": self.fit_values[parms[0]]
              }
        
        p2 = {"id": parms[1],
              "bool": self.fit_bool[parms[1]],
              "sign": ( +1 if id2==2 else -1), 
              "value": self.fit_values[parms[1]]
              }
        
        return p1, p2

    @property
    def operator(self):
        strval = [ it for it in self.constraint if not isinstance(it, (int, long))]
        return strval[0]

    @property
    def offset(self):
        return float(self.constraint[-1])

    def update_fit_bounds(self):
        """
        Update the bounds with the given constraint. This only applies
        if one of the parameters is not varied during fitting.
        
        Notes
        -----
        The fitting boundaries are updated in-place (`fit_bounds` variable
        from `__init__`).
        """
        p1, p2 = self.parameters
        op = self.operator
        os = self.offset
        assert op in ["<", ">"], "Constraint operator not supported"
        
        
        if p1["bool"] and p2["bool"]:
            # do nothing, this case is handled in `get_lmfit_parameter_kwargs`
            pass
        elif p1["bool"]:
            # only parameter 1 is varied
            if op == "<":
                # [3, "<", 1, "0"] -> p1 < p2
                # [3, 1, "<", "0"] -> p1 < -p2
                # [3, 1, "<", "1.2] -> p1 < -p2 + 1.2
                # [3, "<", 1, "1.2] -> p1 < p2 + 1.2
                bnd = [-np.inf, p2["sign"]*p2["value"] + os]
            else:
                # [3, ">", 1, "0"] -> p1 > p2
                # [3, 1, ">", "0"] -> p1 > -p2
                # [3, 1, ">", "1.2] -> p1 > -p2 + 1.2
                # [3, ">", 1, "1.2] -> p1 > p2 + 1.2
                bnd = [p2["sign"]*p2["value"] + os, np.inf]
            bound = [max(self.fit_bounds[p1["id"]][0], bnd[0]),
                     min(self.fit_bounds[p1["id"]][1], bnd[1]),
                     ]
            self.fit_bounds[p1["id"]] = bound
        elif p2["bool"]:
            # only parameter2 is varied
            if op == "<":
                # [3, "<", 1, "0"] -> p2 > p1
                # [3, 1, "<", "0"] -> (-)p2 > p1 -> p2 < -p1
                # [3, 1, "<", "1.2] -> p2 < -p1 + 1.2 = -(p1-1.2)
                # [3, "<", 1, "1.2] -> p2 > p1 - 1.2 = +(p1-1.2)
                if p2["sign"] == -1:
                    bnd = [-np.inf, -(p1["value"] - os)]
                else:
                    bnd = [(p1["value"] - os), np.inf]
            else:
                # [3, ">", 1, "0"] -> p2 < p1
                # [3, 1, ">", "0"] -> p2 > -p1
                # [3, 1, ">", "1.2] -> p2 > -(p1 - 1.2)
                # [3, ">", 1, "1.2] -> p2 < p1 - 1.2
                if p2["sign"] == -1:
                    bnd = [-(p1["value"] - os), np.inf]
                else:
                    bnd = [-np.inf, p1["value"] - os]
            bound = [max(self.fit_bounds[p2["id"]][0], bnd[0]),
                     min(self.fit_bounds[p2["id"]][1], bnd[1]),
                     ]
            self.fit_bounds[p2["id"]] = bound
        else:
            # neither is varied.
            # Do nothing.
            pass
        return self.fit_bounds

    def get_lmfit_parameter_kwargs(self):
        """
        Using the given constraint, update the list of lmfit
        parameters.
        """
        p1, p2 = self.parameters
        op = self.operator
        ofs = self.offset
        assert op in ["<", ">"], "Constraint operator not supported"
        
        
        if p1["bool"] and p2["bool"]:
            if op == "<":
                #p1 < (-)p2 + 1.2
                #-> p1 = (-)p2 - d12 + 1.2
                #-> d12 = (-)p2 - p1 + 1.2
                #-> d12 > 0
                deltaname = "delta_{}_{}".format(p1["id"], p2["id"])
                kwdelt = {}
                kwdelt["name"] = deltaname            
                kwdelt["value"] = p2["bool"]*self.fit_values[p2["id"]] - self.fit_values[p1["id"]] 
                kwdelt["vary"] = True
                kwdelt["min"] = 0 # note: enforces "<=" (not "<")
                kwdelt["max"] = np.inf
                
                kwp1 = {}
                kwp1["name"] = "parm{:04d}".format(p1["id"])
                # this condition deals with negative numbers
                kwp1["expr"] = "{MIN} if {COMP} < {MIN} else {MAX} if {COMP} > {MAX} else {COMP}".format(
                                COMP="{}*parm{:04d}-{}+{:.14f}".format(p2["sign"], p2["id"], deltaname, ofs),
                                MIN=self.fit_bounds[p1["id"]][0],
                                MAX=self.fit_bounds[p1["id"]][1])
                kwargs = [kwdelt, kwp1]
            elif op == ">":
                #p1 > (-)p2 + 1.2
                #-> p1 = (-)p2 + d12 + 1.2
                #-> d12 = p1 - (-)p2  - 1.2
                #-> d12 > 0
                deltaname = "delta_{}_{}".format(p1["id"], p2["id"])
                kwdelt = {}
                kwdelt["name"] = deltaname            
                kwdelt["value"] = self.fit_values[p1["id"]] - p2["bool"]*self.fit_values[p2["id"]]
                kwdelt["vary"] = True
                kwdelt["min"] = 0 # note: enforces ">=" (not ">")
                kwdelt["max"] = np.inf #self.fit_bounds[p1["id"]][1] + max(-p2["sign"]*self.fit_bounds[p2["id"]]) - ofs
                
                kwp1 = {}
                kwp1["name"] = "parm{:04d}".format(p1["id"])
                # this condition deals with negative numbers
                kwp1["expr"] = "{MIN} if {COMP} < {MIN} else {MAX} if {COMP} > {MAX} else {COMP}".format(
                                COMP="{}*parm{:04d}+{}+{:.14f}".format(p2["sign"], p2["id"], deltaname, ofs),
                                MIN=self.fit_bounds[p1["id"]][0],
                                MAX=self.fit_bounds[p1["id"]][1])
                
                kwargs = [kwdelt, kwp1]
                
        else:
            kwargs = None
        
        return kwargs
            
            

class Fit(object):
    """ Used for fitting FCS data to models.
    """
    def __init__(self, correlations=[], global_fit=False,
                 global_fit_variables=[],
                 uselatex=False, verbose=0):
        """ Using an FCS model, fit the data of shape (N,2).


        Parameters
        ----------
        correlations: list of instances or instance of `pycorrfit.Correlation`
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
        
        if not isinstance(correlations, list):
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
                # save fit data in correlation class
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
                # save fit data in correlation class
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
             "fit result" : 1*c.fit_parameters,
             "fit parameters" : 1*np.where(c.fit_parameters_variable)[0],
             "fit weights" : 1*self.compute_weights(c)
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
        #
        # Constraints have the three-element form:
        #   [1, "<", 0] -> parm1 < parm0
        #   [3, ">", 1] -> parm3 > parm1
        # or the four-element form:
        #   [1, "<", 0, "2.3"]] -> parm1 < parm0 + 2.3
        #   [1, 0, "<", "2.3"]] -> parm1 + parm0 < 2.3
        for pp in range(len(self.fit_parm)):
            if self.fit_bool[pp]:
                inconstr = len([ cc for cc in self.constraints if pp in cc])
                kwarglist = []

                if inconstr:
                    for cc in self.constraints:
                        con = Constraint(constraint=cc,
                                         fit_bool=self.fit_bool,
                                         fit_bounds=self.fit_bound,
                                         fit_values=self.fit_parm)
                        self.fit_bound = con.update_fit_bounds()
                        if con.parameters[0]["id"] == pp:
                            kws = con.get_lmfit_parameter_kwargs()
                            if kws is not None:
                                kwarglist += kws
                if len(kwarglist) == 0:
                    # normal parameter
                    kwarglist += [{"name": "parm{:04d}".format(pp),
                                  "value": self.fit_parm[pp],
                                  "vary": True,
                                  "min": self.fit_bound[pp][0],
                                  "max": self.fit_bound[pp][1],
                                   }]
                for kw in kwarglist:
                    params.add(lmfit.Parameter(**kw))

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
