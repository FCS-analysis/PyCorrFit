# -*- coding: utf-8 -*-
u"""PyCorrFit - module "models"

Define all models and set initial parameters.

Each model has a unique ID. This ID is very important:
    1. It is a wxWidgets ID.
    2. It is used in the saving of sessions to identify a model.
It is very important, that model IDs do NOT change in newer versions
of PyCorrFit, because it would not be possible to restore older
PyCorrFit sessions.

Dimensionless representation:
unit of time        : 1 ms
unit of inverse time: 10³ /s
unit of distance    : 100 nm
unit of Diff.coeff  : 10 µm²/s
unit of inverse area: 100 /µm²
unit of inv. volume : 1000 /µm³
"""


# This file is necessary for this folder to become a module that can be 
# imported from within Python/PyCorrFit.

import copy
import numpy as np
import sys
import warnings


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
            self._boundaries = [[None,None]]*len(self._parameters[1])
        
        if "Constraints" in list(datadict.keys()):
            # sort constraints such that the first value is always
            # larger than the last.
            newcc = []
            for cc in datadict["Constraints"]:
                if cc[0] < cc[2]:
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
        warnings.warn("`func_verification is deprecated: please do not use it!")
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
        for item in  self.get_supplementary_parameters(values, countrate):
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
    



def AppendNewModel(Modelarray):
    """ Append a new model from a modelarray. *Modelarray* has to be a list
        whose elements have two items:
        [0] parameters
        [1] some info about the model
        See separate models for more information
    """
    global values
    global valuedict
    global models
    global modeldict
    global supplement
    global boundaries
    global modeltypes

    for datadict in Modelarray:
        # We can have many models in one model array
        amod = Model(datadict)

        models.append(amod)
        modeldict[amod.id] = amod

        values.append(amod.parameters)
        valuedict[amod.id] = amod.parameters

        # Supplementary Data might be there
        supplement[amod.id] = amod.func_supplements

        # Check functions - check for correct values
        boundaries[amod.id] = amod.boundaries

        # Add model type to internal type list.
        if amod.type is not None:
            if not amod.type in modeltypes:
                modeltypes[amod.type] = []
            modeltypes[amod.type].append(amod.id)

def GetHumanReadableParms(model, parameters):
    """ From a set of parameters that have internal units e.g. [100 nm],
        Calculate the parameters in human readable units e.g. [nm].
        Uses modeldict from this module.
        *model* - an integer ID of a model
        *parameters* - a list/array of parameters 
                       (all parameters of that model)
        Returns:
        New Units, New Parameters
    """
    stdparms = valuedict[model]
    if len(stdparms) == 5:
        # This means we have extra information on the model
        # Return some human readable stuff
        OldParameters = 1.*np.array(parameters)
        Facors = 1.*np.array(stdparms[4])
        NewParameters = 1.*OldParameters*Facors
        NewUnits = stdparms[3]
        return NewUnits, NewParameters
    else:
        # There is no info about human readable stuff, or it is already human
        # readable.
        return stdparms[0], parameters


def GetHumanReadableParameterDict(model, names, parameters):
    """ From a set of parameters that have internal units e.g. [100 nm],
        Calculate the parameters in human readable units e.g. [nm].
        Uses modeldict from this module.
        In contrast to *GetHumanReadableParms* this function accepts
        single parameter names and does not need the full array of
        parameters.
        *model* - an integer ID of a model
        *name* - the names of the parameters to be translated,
                 order should be same as in
        *parameters* - a list of parameters
        Returns:
        New Units, New Parameters
    """
    stdparms = valuedict[model]
    if len(stdparms) == 5:
        # This means we have extra information on the model
        # Return some human readable stuff
        # Check for list:
        if isinstance(names, basestring):
            names = [names]
            parameters = [parameters]
            retstring = True
        else:
            retstring = False
        # Create new lists
        NewUnits = list()
        NewParameters = list()
        for i in np.arange(len(stdparms[0])):
            for j in np.arange(len(names)):
                if names[j] == stdparms[0][i]:
                    NewUnits.append(stdparms[3][i])
                    NewParameters.append(stdparms[4][i]*parameters[j])
        if retstring == True:
            NewUnits = NewUnits[0]
            NewParameters = NewParameters[0]
        return NewUnits, NewParameters
    else:
        # There is no info about human readable stuff, or it is already human
        # readable.
        return names, parameters


def GetInternalFromHumanReadableParm(model, parameters):
    """ This is the inverse of *GetHumanReadableParms*
        *model* - an integer ID of a model
        *parameters* - a list/array of parameters 
        Returns:
        New Units, New Parameters
    """
    stdparms = valuedict[model]
    if len(stdparms) == 5:
        # This means we have extra information on the model
        # and can convert to internal values
        OldParameters = 1.*np.array(parameters)
        Facors = 1./np.array(stdparms[4])        # inverse
        NewParameters = 1.*OldParameters*Facors
        NewUnits = stdparms[0]
        return NewUnits, NewParameters
    else:
        # There is no info about human readable stuff. The given 
        # parameters have not been converted befor using
        # *GetHumanReadableParms*.
        return stdparms[0], parameters
        

def GetModelType(modelid):
    """ Given a modelid, get the type of model function
        (Confocal, TIR-Conf., TIR-□, User)
    """
    if modelid >= 7000:
        return u"User"
    else:
        shorttype = dict()
        shorttype[u"Confocal (Gaussian)"] = u"Confocal"
        shorttype[u"TIR (Gaussian/Exp.)"] = u"TIR Conf."
        shorttype[u"TIR (□xσ/Exp.)"] = u"TIR □xσ"
        for key in modeltypes.keys():
            mlist = modeltypes[key]
            if mlist.count(modelid) == 1:
                return shorttype[key]
                try:
                    return shorttype[key]
                except:
                    return ""

def GetModelFunctionFromId(modelid):
    return modeldict[modelid][3]
    

def GetModelParametersFromId(modelid):
    return valuedict[modelid][1]


def GetModelFitBoolFromId(modelid):
    return valuedict[modelid][2]

def GetMoreInfo(modelid, Page):
    """ This functino is called by someone who has already calculated
        some stuff or wants to know more about the model he is looking at.
        *modelid* is an ID of a model.
        *Page* is a wx.flatnotebook page.
        Returns:
         More information about a model in form of a list.
    """
    # Background signal average
    bgaverage = None
    # Get the parameters from the current page.
    parms = Page.active_parms[1]
    Info = list()
    corr = Page.corr
    if corr.is_ac:
        if len(corr.traces)==1:
            countrate = corr.traces[0].countrate
        else:
            countrate = None
        ## First import the supplementary parameters of the model
        ## The order is important for plot normalization and session
        ## saving as of version 0.7.8
        # Try to get the dictionary entry of a model
        # Background information
        if len(corr.backgrounds)==1:
            bgaverage = corr.backgrounds[0].countrate
            # Now set the correct countrate
            # We already printed the countrate, so there's no harm done.
        if countrate is not None and bgaverage is not None:
            # might be that there is no countrate.
            relativecountrate = countrate - bgaverage
        else:
            relativecountrate = countrate
        # In case of cross correlation, we don't show this kind of
        # information.
        try:
            # This function should return all important information
            # that can be calculated from the given parameters.
            # We need the relativecountrate to compute the CPP.
            func_info = supplement[modelid]
            data = func_info(parms, relativecountrate)
            for item in data:
                Info.append([item[0], item[1]])
        except KeyError:
            # No information available
            pass
        if countrate is not None:
            # Measurement time
            duration = corr.traces[0].duration/1000
            Info.append(["duration [s]", duration])
            # countrate has to be printed before background.
            # Background might overwrite countrate.
            Info.append(["avg. signal [kHz]", corr.traces[0].countrate])
    else:
        ## Cross correlation curves usually have two traces. Since we
        ## do not know how to compute the cpp, we will pass the argument
        ## "None" as the countrate.
        ## First import the supplementary parameters of the model
        ## The order is important for plot normalization and session
        ## saving as of version 0.7.8
        # Try to get the dictionary entry of a model
        try:
            # This function should return all important information
            # that can be calculated from the given parameters.
            func_info = supplement[modelid]
            data = func_info(parms, None)
            for item in data:
                Info.append([item[0], item[1]])
        except KeyError:
            # No information available
            pass
        if len(corr.traces)==2:
            # Measurement time
            duration = corr.traces[0].duration/1000
            Info.append(["duration [s]", duration])
            # countrate has to be printed before background.
            # Background might overwrite countrate.
            Info.append(["avg. signal A [kHz]", corr.traces[0].countrate])
            Info.append(["avg. signal B [kHz]", corr.traces[1].countrate])

    if len(Info) == 0:
        # If nothing matched until now:
        return None
    else:
        return Info


def GetPositionOfParameter(model, name):
    """ Returns an integer corresponding to the position of the label
        of a parameter in the model function
    """
    stdparms = valuedict[model]
    for i in np.arange(len(stdparms[0])):
        if name == stdparms[0][i]:
            return int(i)
    

def model_setup(modelid, name, comp, mtype, fctn, par_labels, par_values,
                par_vary=None, par_boundaries=None, par_constraints=None,
                par_hr_labels=None, par_hr_factors=None,
                supplementary_method=None,
                ):
    u"""
    This helper method does everything that is required to make a model
    available for PyCorrFit. The idea is that this method can be called from
    anywhere and thus we do not need to do the tedious work of adding models
    in the __init__.py file.
    
    Parameters
    ----------
    modelid : int
        Model identifier.
    name : str
        Name of the Model.
    comp : str
        Description of components of the model, e.g. "T+3D+2D"
    mtype : str
        Type of model, e.g. "Confocal (Gaussian)"
    fctn : callable
        The method that computes the model function. It must take
        two arguments. The first is of shape `par_values` and the
        second is a 2D array containing lag time and correlation.
    par_labels : list-like, strings
        The labels of each parameter in PyCorrFit dimensionless
        representation, i.e.
        
            unit of time        : 1 ms
            unit of inverse time: 1000 /s
            unit of distance    : 100 nm
            unit of Diff.coeff  : 10 µm²/s
            unit of inverse area: 100 /µm²
            unit of inv. volume : 1000 /µm³
    par_values : list-like, floats
        The parameter values in PyCorrFit dimensionless units.
    par_vary :  list-like, bools or None
        A list describing which parameters should be varied during
        fitting. If not given, only the first element is set to `True`.
    par_boundaries : list-like, floats
        The parameter boundaries - two values for each parameter.
        Examples: [[0, np.inf], [0,1]]
    par_constraints : list of lists
        Constraints between parameters. For example, make sure parameter
        2 is always larger than parameter 1 and parameter 5 is always
        smaller than parameter 1: [[2, ">", 1], [5, "<", 1]]
        Parameter count starts at 0.
    par_hr_labels : list-like, strings
        User-defined human readable labels of the parameters. If this is
        set, `par_hr_factors` is also required.
    par_hr_factors : list-like, floats
        The multiplicative factors to get from `par_labels` to
        `par_hr_labels`.
    supplementary_method : callable
        A method that takes the parameters `par_values` and the countrate
        of the experiment as an argument and returns a dictinoary of
        supplementary information.
    """
    # Checks
    assert len(par_labels) == len(par_values)
    for p in [par_vary,
              par_boundaries,
              par_constraints,
              par_hr_labels,
              par_hr_factors,
              ]:
        if p is not None:
            assert len(p) == len(par_values), "Number of parameters must match!"
    if par_hr_factors is None or par_hr_labels is None:
        assert par_hr_factors is None, "human readable requires two parameter"
        assert par_hr_labels is None, "human readable requires two parameter"
    
    if par_vary is None:
        # Set par_vary
        par_vary = np.zeros(len(par_values), dtype=bool)
        par_vary[0] = True
    
    if par_hr_factors is None:
        # Set equal to labels
        par_hr_labels = par_labels
        par_hr_factors = np.ones_like(par_values)
    
    model={}
    
    model["Parameters"] = [par_labels, par_values, par_vary,
                           par_hr_labels, par_hr_factors]
    
    model["Definitions"] = [modelid, comp, name, fctn, mtype]
    
    if supplementary_method is not None:
        model["Supplements"] = supplementary_method
    
    if par_boundaries is not None:
        model["Boundaries"] = par_boundaries
    
    if par_constraints is not None:
        model["Constraints"] = par_constraints
    
    AppendNewModel([model])
    
   

# Pack all variables
values = list()
# Also create a dictionary, key is modelid
valuedict = dict()
# Pack all models
models = list()
# Also create a dictinary
modeldict = dict()
# A dictionary for supplementary data:
supplement = dict()
# A dictionary containing model boundaries
boundaries = dict()


# Create a list for the differentiation between the models
# This should make everything look a little cleaner
modeltypes = dict()
#modeltypes[u"Confocal (Gaussian)"] = [6001, 6002, 6012, 6011, 6031, 6032, 6030]
#modeltypes[u"TIR (Gaussian/Exp.)"] = [6013, 6033, 6034]
#modeltypes[u"TIR (□xσ/Exp.)"] = [6000, 6010, 6022, 6020, 6023, 6021]

modeltypes[u"Confocal (Gaussian)"] = [6011, 6030, 6002, 6031, 6032, 6043]
modeltypes[u"TIR (Gaussian/Exp.)"] = [6014, 6034, 6033]
modeltypes[u"TIR (□xσ/Exp.)"] = [6010, 6023, 6000, 6022, 6020, 6021]
modeltypes[u"User"] = []


## Models
from . import MODEL_classic_gaussian_2D
from . import MODEL_classic_gaussian_3D
from . import MODEL_classic_gaussian_3D2D
from . import MODEL_classic_gaussian_TT3D3D
from . import MODEL_TIRF_gaussian_1C
from . import MODEL_TIRF_gaussian_3D2D
from . import MODEL_TIRF_gaussian_3D3D
from . import MODEL_TIRF_1C
from . import MODEL_TIRF_2D2D
from . import MODEL_TIRF_3D2D
from . import MODEL_TIRF_3D3D
from . import MODEL_TIRF_3D2Dkin_Ries

# Load all models from the imported "MODEL_*" submodules
# These are the models that were not imported using the `model_setup` method.
for g in list(globals().keys()):
    if g.startswith("MODEL_") and hasattr(globals()[g], "Modelarray"):
        AppendNewModel(globals()[g].Modelarray)
