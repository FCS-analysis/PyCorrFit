# -*- coding: utf-8 -*-
"""
    PyCorrFit

    Module models:
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


# This file is necessary for this folder to become a module that can be 
# imported from within Python/PyCorrFit.

import numpy as np                  # NumPy
import sys


## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
reload(sys)
sys.setdefaultencoding('utf-8')


## Models
from . import MODEL_classic_gaussian_2D
from . import MODEL_classic_gaussian_3D
from . import MODEL_classic_gaussian_3D2D
from . import MODEL_TIRF_gaussian_1C
from . import MODEL_TIRF_gaussian_3D2D
from . import MODEL_TIRF_gaussian_3D3D
from . import MODEL_TIRF_1C
from . import MODEL_TIRF_2D2D
from . import MODEL_TIRF_3D2D
from . import MODEL_TIRF_3D3D
from . import MODEL_TIRF_3D2Dkin_Ries

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
    global verification

    for Model in Modelarray:
        # We can have many models in one model array
        parms = Model["Parameters"]
        texts = Model["Definitions"]
        values.append(parms)
        # model ID is texts[0]
        valuedict[texts[0]] = parms
        models.append(texts)
        modeldict[texts[0]] = texts
        # Suplementary Data might be there
        try:
             supper = Model["Supplements"]
        except KeyError:
            # Nothing to do
            pass
        else:
            supplement[texts[0]] = supper
        # Check functions - check for correct values
        try:
             verify = Model["Verification"]
        except KeyError:
            # Nothing to do. Return empty function, so we do not need to
            # do this try and error thing again.
            verification[texts[0]] = lambda parms: parms
        else:
            verification[texts[0]] = verify


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
    # Signal countrate/average:
    # might become countrate - bgaverage
    countrate = Page.traceavg
    # Get the parameters from the current page.
    parms = Page.active_parms[1]
    Info = list()
    if Page.IsCrossCorrelation is False:
        ## First import the supplementary parameters of the model
        ## The order is important for plot normalization and session
        ## saving as of version 0.7.8
        # Try to get the dictionary entry of a model
        # Background information
        if Page.bgselected is not None:
            # Background list consists of items with
            #  [0] average
            #  [1] name
            #  [2] trace
            bgaverage = Page.parent.Background[Page.bgselected][0]
            # Now set the correct countrate
            # We already printed the countrate, so there's no harm done.
            if countrate is not None:
                # might be that there is no countrate.
                countrate = countrate - bgaverage
        try:
            # This function should return all important information
            # that can be calculated from the given parameters.
            func_info = supplement[modelid]
            data = func_info(parms, countrate)
            for item in data:
                Info.append([item[0], item[1]])
        except KeyError:
            # No information available
            pass
        # In case of cross correlation, we don't show this kind of
        # information.
        if Page.traceavg is not None:
            # Measurement time
            duration = Page.trace[-1,0]/1000
            Info.append(["duration [s]", duration])
            # countrate has to be printed before background.
            # Background might overwrite countrate.
            Info.append(["avg. signal [kHz]", Page.traceavg])
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
        if Page.tracecc is not None:
            # Measurement time
            duration = Page.tracecc[0][-1,0]/1000
            Info.append(["duration [s]", duration])
            # countrate has to be printed before background.
            # Background might overwrite countrate.
            avg0 = Page.tracecc[0][:,1].mean()
            avg1 = Page.tracecc[1][:,1].mean()
            Info.append(["avg. signal A [kHz]", avg0])
            Info.append(["avg. signal B [kHz]", avg1])


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
# A dictionary for checking for correct variables
verification = dict()


# 6001 6002 6031
AppendNewModel(MODEL_classic_gaussian_2D.Modelarray)

# 6011 6012 6030
AppendNewModel(MODEL_classic_gaussian_3D.Modelarray)

# 6032
AppendNewModel(MODEL_classic_gaussian_3D2D.Modelarray)

# 6013 6014
AppendNewModel(MODEL_TIRF_gaussian_1C.Modelarray)

# 6033
AppendNewModel(MODEL_TIRF_gaussian_3D2D.Modelarray)

# 6034
AppendNewModel(MODEL_TIRF_gaussian_3D3D.Modelarray)

# 6000 6010
AppendNewModel(MODEL_TIRF_1C.Modelarray)

# 6022
AppendNewModel(MODEL_TIRF_2D2D.Modelarray)

# 6020
AppendNewModel(MODEL_TIRF_3D2D.Modelarray)

# 6023
AppendNewModel(MODEL_TIRF_3D3D.Modelarray)

# 6021
AppendNewModel(MODEL_TIRF_3D2Dkin_Ries.Modelarray) 



# Create a list for the differentiation between the models
# This should make everything look a little cleaner
modeltypes = dict()
#modeltypes[u"Confocal (Gaussian)"] = [6001, 6002, 6012, 6011, 6031, 6032, 6030]
#modeltypes[u"TIR (Gaussian/Exp.)"] = [6013, 6033, 6034]
#modeltypes[u"TIR (□xσ/Exp.)"] = [6000, 6010, 6022, 6020, 6023, 6021]

modeltypes[u"Confocal (Gaussian)"] = [6011, 6030, 6002, 6031, 6032]
modeltypes[u"TIR (Gaussian/Exp.)"] = [6014, 6034, 6033]
modeltypes[u"TIR (□xσ/Exp.)"] = [6010, 6023, 6000, 6022, 6020, 6021]
modeltypes[u"User"] = list()

