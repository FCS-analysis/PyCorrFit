"""PyCorrFit data set:  Classes for FCS data evaluation."""
import hashlib
import warnings

import numpy as np

from . import models as mdls
from . import fit
from .trace import Trace


class Correlation(object):
    """ unifies correlation curve handling
    """

    def __init__(self, backgrounds=[], correlation=None, corr_type="AC",
                 filename=None, fit_algorithm="Lev-Mar",
                 fit_model=6000, fit_ival=(0, 0),
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
        if channel not in [0, 1]:
            raise ValueError("`channel` must be '0' or '1'!")
        if not isinstance(background, Trace):
            raise ValueError("`background` must be instance of `Trace`")

        if self.is_ac:
            if channel == 1:
                raise ValueError("Cannot set second background for AC.")
            self._backgrounds = [background]
        else:
            if len(self._backgrounds) == 0:
                self._backgrounds = [Trace(countrate=0, duration=0),
                                     Trace(countrate=0, duration=0)]
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
        if len(value) > 2:
            raise ValueError("Backgrounds length must not exceed 2.")

        for v in value:
            if isinstance(v, np.ndarray):
                backgrounds.append(Trace(trace=v))
            elif isinstance(v, Trace):
                backgrounds.append(v)
            else:
                raise ValueError(
                    "Each background must be instance of Trace or ndarray")
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
        p = 1. * np.array(parms)
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
            corr[:, 1] *= self.bg_correction_factor
            # perform parameter normalization
            return corr[self.fit_ival[0]:self.fit_ival[1], :]

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
            corr[:, 1] *= self.normalize_factor
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

        if value not in list(fit.Algorithms.keys()):
            raise ValueError("Invalid fit algorithm: {}".format(value))

        self._fit_algorithm = value

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
    def fit_model(self):
        """instance of a fit model"""
        return self._fit_model

    @fit_model.setter
    def fit_model(self, value):
        """set the fit model
        """
        if isinstance(value, int):
            newmodel = mdls.modeldict[value]
        elif isinstance(value, mdls.Model):
            newmodel = value
        else:
            raise NotImplementedError("Unknown model identifier")

        if newmodel != self._fit_model:
            self._fit_model = newmodel
            # overwrite fitting parameters
            self._fit_parameters = self._fit_model.default_values
            self._fit_parameters_variables = self._fit_model.default_variables
            self._fit_parameters_range = np.zeros(
                (len(self._fit_parameters), 2))
            self.normparm = None

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
        # some methods of PyCorrFit depend on the array being
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
        expect_shape = (self.fit_parameters.shape[0], 2)
        if value.shape != expect_shape:
            msg = "Expected shape of fit parameters: {} (vs {})".format(
                expect_shape, value.shape
            )
            raise ValueError(msg)
        self._fit_parameters_range = value

    @property
    def fit_parameters_variable(self):
        """which parameters are variable during fitting"""
        if self._fit_parameters_variable is None:
            self._fit_parameters_variable = np.array(
                self.fit_model.default_variables, dtype=bool)
        return self._fit_parameters_variable

    @fit_parameters_variable.setter
    def fit_parameters_variable(self, value):
        value = np.array(value, dtype=bool)
        expect_size = self.fit_parameters.shape[0]
        if value.shape[0] != expect_size:
            msg = "Fit parameter variables must have size {}!".format(
                expect_size)
            raise ValueError(msg)
        self._fit_parameters_variable = value

    @property
    def lag_time(self):
        """logarithmic lag time axis"""
        if self.correlation is not None:
            return self._correlation[:, 0].copy()
        elif self._lag_time is not None:
            return self._lag_time
        else:
            # some default lag time
            return 10**np.linspace(-6, 8, 1001)

    @lag_time.setter
    def lag_time(self, value):
        if self.correlation is not None:
            warnings.warn(
                "Setting lag time not possible, because of existing correlation")
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
        modeled[:, 0] = lag
        modeled[:, 1] = self.fit_model(self.fit_parameters, lag)
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
        toplot[:, 1] *= self.normalize_factor
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
        residuals[:, 1] -= self.modeled[:, 1]
        return residuals

    @property
    def residuals_fit(self):
        """fit residuals, same shape as self.correlation_fit"""
        residuals_fit = self.correlation_fit.copy()
        residuals_fit[:, 1] -= self.modeled_fit[:, 1]
        return residuals_fit

    @property
    def residuals_plot(self):
        """fit residuals, same shape as self.correlation_fit"""
        cp = self.correlation_plot
        if cp is not None:
            residuals_plot = self.correlation_plot.copy()
            residuals_plot[:, 1] -= self.modeled_plot[:, 1]
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
        if len(value) > 2:
            raise ValueError("Traces length must not exceed 2.")
        for v in value:
            if isinstance(v, np.ndarray):
                traces.append(Trace(trace=v))
            elif isinstance(v, Trace):
                traces.append(v)
            else:
                raise ValueError(
                    "Each trace must be instance of Trace or ndarray")
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
            hasher.update(str(np.random.random()).encode())
            hasher.update(str(self._correlation).encode())
            hasher.update(str(self.filename).encode())
            hasher.update(str(self.title).encode())
            self._uid = hasher.hexdigest()
        return self._uid
