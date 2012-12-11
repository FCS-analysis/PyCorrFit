# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module models:
    Define all models and set initial parameters.

    Each model has a unique ID. This ID is very important:
        1. It is a wxWidgets ID.
        2. It is used in the saving of sessions to identify a model.
    It is very important, that model IDs do NOT change in newer versions of
    this program, because it would not be possible to restore older PyCorrFit
    sessions (Unless you add a program that maps the model IDs to the correct
    models).

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


# This file is necessary for this folder to become a module that can be 
# imported by PyCorrFit or other people.

import numpy as np                  # NumPy
import platform
import sys


## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
reload(sys)
sys.setdefaultencoding('utf-8')


## Models
import MODEL_classic_gaussian_2D
import MODEL_classic_gaussian_3D
import MODEL_classic_gaussian_3D2D
import MODEL_TIRF_gaussian_1C
import MODEL_TIRF_gaussian_3D2D
import MODEL_TIRF_gaussian_3D3D
import MODEL_TIRF_1C
import MODEL_TIRF_2D2D
import MODEL_TIRF_3D2D
import MODEL_TIRF_3D3D
import MODEL_TIRF_3D2Dkin_Ries

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
            a = 0
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
    """ From a set of parameters that have some strange units e.g. [100 nm],
        Calculate the parameters in human readable units e.g. [nm].
        Uses modeldict from this module.
        *model* - an integer ID of a model
        *parameters* - a list/array of parameters (all parameters of that model)
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
    """ From a set of parameters that have some strange units e.g. [100 nm],
        Calculate the parameters in human readable units e.g. [nm].
        Uses modeldict from this module.
        *model* - an integer ID of a model
        *name of parameters* - order should be same as in
        *parameters* - a list of parameters
        Returns:
        New Units, New Parameters
    """
    stdparms = valuedict[model]
    if len(stdparms) == 5:
        # This means we have extra information on the model
        # Return some human readable stuff
        NewUnits = list()
        NewParameters = list()
        for i in np.arange(len(stdparms[0])):
            for j in np.arange(len(names)):
                if names[j] == stdparms[0][i]:
                    NewUnits.append(stdparms[3][i])
                    NewParameters.append(stdparms[4][i]*parameters[j])
        return NewUnits, NewParameters
    else:
        # There is no info about human readable stuff, or it is already human
        # readable.
        return names, parameters


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
    # Some Trace information:
    if Page.IsCrossCorrelation is False:
        # In case of cross correlation, we don't show this kind of
        # information.
        if Page.traceavg is not None:
            # Measurement time
            duration = Page.trace[-1,0]/1000
            Info.append(["duration [s]", duration])
            # countrate has to be printed before background.
            # Background might overwrite countrate.
            Info.append(["avg. signal [kHz]", Page.traceavg])
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

        # Try to get the dictionary entry of a model
        try:
            # This function should return all important information
            # that can be calculated from the given parameters.
            func_info = supplement[modelid]
            data = func_info(parms, countrate)
            for item in data:
                Info.append([item[0], item[1]])
        except KeyError:
            # No information available
            a=0
    else:
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
# 6013
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
modeltypes[u"Classic (Gauß)"] = [6001, 6002, 6012, 6011, 6031, 6032, 6030]
modeltypes[u"TIR-FCS (Gauß/exp)"] = [6013, 6033, 6034]
modeltypes[u"TIR-FCS (□xσ/exp)"] = [6000, 6010, 6022, 6020, 6023, 6021]
modeltypes["User"] = list()

