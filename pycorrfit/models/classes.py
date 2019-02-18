import copy
import numbers
import warnings

import numpy as np


class Model(object):
    """General class for handling FCS fitting models"""

    def __init__(self, datadict):
        """datadict is an item in Modelarray"""
        self._parameters = datadict["Parameters"]
        self._definitions = datadict["Definitions"]

        if "Supplements" in list(datadict.keys()):
            self._supplements = datadict["Supplements"]
        else:
            self._supplements = lambda x, y: []

        if "Boundaries" in list(datadict.keys()):
            self._boundaries = datadict["Boundaries"]
        else:
            # dummy verification function
            self._boundaries = [[-np.inf, np.inf]]*len(self._parameters[1])

        if "Constraints" in list(datadict.keys()):
            # sort constraints such that the first value is always
            # larger than the last.
            newcc = []
            for cc in datadict["Constraints"]:
                # check for integral numbers to avoid comparison to strings
                # in e.g. confocal t_3d_3d_3d model.
                if (isinstance(cc[0], numbers.Integral) and
                    isinstance(cc[2], numbers.Integral) and
                        cc[0] < cc[2]):
                    if cc[1] == ">":
                        cc = [cc[2], "<", cc[0]]
                    elif cc[1] == "<":
                        cc = [cc[2], ">", cc[0]]
                newcc.append(cc)
            self._constraints = newcc
        else:
            self._constraints = []

    def __call__(self, parameters, tau):
        return self.function(parameters, tau)

    def __getitem__(self, key):
        """Emulate old list behavior of models"""
        return self._definitions[key]

    def __repr__(self):
        text = "Model {} - {}".format(
            self.id,
            self.description_short)
        return text

    def apply(self, parameters, tau):
        """
        Apply the model with `parameters` and lag
        times `tau`
        """
        return self.function(parameters, tau)

    @property
    def boundaries(self):
        return self._boundaries

    @property
    def constraints(self):
        """ fitting constraints """
        return copy.copy(self._constraints)

    @property
    def components(self):
        """how many components does this model have"""
        return self._definitions[1]

    @property
    def default_values(self):
        """default fitting values"""
        return np.array(self._parameters[1]).copy()

    @property
    def default_variables(self):
        """indexes default variable fitting (bool)"""
        return np.array(self._parameters[2]).copy()

    @property
    def description_long(self):
        """long description"""
        return self._definitions[3].__doc__

    @property
    def description_short(self):
        """short description"""
        return self._definitions[2]

    @property
    def function(self):
        return self._definitions[3]

    @property
    def func_supplements(self):
        return self._supplements

    @property
    def func_verification(self):
        warnings.warn(
            "`func_verification is deprecated: please do not use it!")
        return lambda x: x

    def get_supplementary_parameters(self, values, countrate=None):
        """
        Compute additional information for the model

        Parameters
        ----------
        values: list-like of same length as `self.default_values`
            parameters for the model
        countrate: float
            countrate in kHz
        """
        return self.func_supplements(values, countrate)

    def get_supplementary_values(self, values, countrate=None):
        """
        Returns only the values of
        self.get_supplementary_parameters

        Parameters
        ----------
        values: list-like of same length as `self.default_values`
            parameters for the model
        countrate: float
            count rate in Hz
        """
        out = list()
        for item in self.get_supplementary_parameters(values, countrate):
            out.append(item[1])
        return out

    @property
    def id(self):
        return self._definitions[0]

    @property
    def name(self):
        return self.description_short

    @property
    def parameters(self):
        return self._parameters

    @property
    def type(self):
        if len(self._definitions) < 5:
            return None
        else:
            return self._definitions[4]
