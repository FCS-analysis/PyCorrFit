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

from .classes import Model
from .control import values, valuedict, models, modeldict, modeltypes, supplement, boundaries, shorttype


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
        for key in modeltypes.keys():
            mlist = modeltypes[key]
            if mlist.count(modelid) == 1:
                try:
                    return shorttype[key]
                except:
                    warnings.warn("No shorttype defined for `{}`.".format(key))
                    return key

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
    

