# -*- coding: utf-8 -*-
u"""  PyCorrFit  - module "readfiles"

Import correlation data from data files.
"""
# This file is necessary for this folder to become a module that can be 
# imported by PyCorrFit.

import csv
import numpy as np
import os
import sys
import tempfile
import yaml
import warnings
import zipfile

# To add a filetype add it here and in the
# dictionaries at the end of this file.
from .read_ASC_ALV import openASC
from .read_CSV_PyCorrFit import openCSV
from .read_SIN_correlator_com import openSIN
from .read_FCS_Confocor3 import openFCS
from .read_mat_ries import openMAT
from .read_pt3_PicoQuant import openPT3



def AddAllWildcard(Dictionary):
    wildcard = ""
    keys = Dictionary.keys()
    N = len(keys)
    i = 0
    for key in keys:
        newwc = key.split("|")[1]
        wildcard = wildcard + newwc
        i = i + 1
        if i != N:
            wildcard = wildcard + ";"

    Dictionary[Allsupfilesstring+"|"+wildcard] = openAny
    return Dictionary


# To increase user comfort, we will now create a file opener thingy that
# knows how to open all files we know.
def openAny(dirname, filename):
    """ Using the defined Filetypes and BGFiletypes, open the given file """
    wildcard = filename.split(".")[-1]
    for key in Filetypes.keys():
        # Recurse into the wildcards
        wildcardstring = key.split("|")
        # We do not want to recurse
        if wildcardstring[0] != Allsupfilesstring:
            otherwcs = wildcardstring[1].split(";")
            for string in otherwcs:
                if string.strip(" .*") == wildcard:
                    return Filetypes[key](dirname, filename)
    # If we could not find the correct function in Filetypes, try again
    # in BGFiletypes:
    return openAnyBG(dirname, filename)
    
    ## For convenience in openZIP
    #return None # already in openAnyBG


def openAnyBG(dirname, filename):
    wildcard = filename.split(".")[-1]
    for key in BGFiletypes.keys():
        wildcardstring = key.split("|")
        # We do not want to recurse
        if wildcardstring[0] != Allsupfilesstring:
            otherwcs = wildcardstring[1].split(";")
            for string in otherwcs:
                if string.strip(" .*") == wildcard:
                    return BGFiletypes[key](dirname, filename)
    # For convenience in openZIP
    return None
    

def openZIP(dirname, filename):
    """ 
        Get everything inside a .zip file that could be an FCS curve.
        Will use any wildcard in Filetypes dictionary.
    """
    #    It's a rather lengthy import of the session file. The code is copied
    #    from openfile.OpenSession. The usual zip file packed curves are
    #    imported on the few code lines after the else statement.

    ## Open the archive:
    Arc = zipfile.ZipFile(os.path.join(dirname, filename), mode='r')
    Correlations = list() # Correlation information
    Curvelist = list()    # Type information
    Filelist = list()     # List of filenames corresponding to *Curvelist*
    Trace = list()        # Corresponding traces
    ## First test, if we are opening a session file
    sessionwc = [".fcsfit-session.zip", ".pcfs"]
    if ( filename.endswith(sessionwc[0]) or
         filename.endswith(sessionwc[1])     ):
        # Get the yaml parms dump:
        yamlfile = Arc.open("Parameters.yaml")
        # Parms: Fitting and drawing parameters of the correlation curve
        # The *yamlfile* is responsible for the order of the Pages #i.
        # The parameters are actually useless to us right now.
        Parms = yaml.safe_load(yamlfile)
        yamlfile.close()
        # Get the correlation arrays
        ImportedNum = list()
        for i in np.arange(len(Parms)):
            # The *number* is used to identify the correct file
            number = str(Parms[i][0])
            expfilename = "data"+number[1:len(number)-2]+".csv"
            expfile = Arc.open(expfilename, 'r')
            readdata = csv.reader(expfile, delimiter=',')
            dataexp = list()
            if str(readdata.next()[0]) == "# tau only":
                # We do not have a curve here
                pass
            else:
                Filelist.append(filename+"/#"+number[1:len(number)-2])
                for row in readdata:
                    # Exclude commentaries
                    if (str(row[0])[0:1] != '#'):
                        dataexp.append((float(row[0]), float(row[1])))
                dataexp = np.array(dataexp)
                Correlations.append(dataexp)
                ImportedNum.append(i)
            del readdata
            expfile.close()
        # Get the Traces
        for i in ImportedNum:   
            # Make sure we only import those traces that had a corresponding
            # correlation curve. (ImportedNum)
            #
            # The *number* is used to identify the correct file
            number = str(Parms[i][0])
            # Find out, if we have a cross correlation data type
            IsCross = False
            try:
                IsCross = Parms[i][7]
            except IndexError:
                # No Cross correlation
                pass
            if IsCross is False:
                tracefilenames = ["trace"+number[1:len(number)-2]+".csv"]
                Curvelist.append("AC")
            else:
                # Cross correlation uses two traces
                tracefilenames = ["trace"+number[1:len(number)-2]+"A.csv",
                                  "trace"+number[1:len(number)-2]+"B.csv" ]
                Curvelist.append("CC")
            thistrace = list()
            for tracefilename in tracefilenames:
                try:
                    Arc.getinfo(tracefilename)
                except KeyError:
                    # No correlation curve, but add a None
                    pass
                else:
                    tracefile = Arc.open(tracefilename, 'r')
                    traceread = csv.reader(tracefile, delimiter=',')
                    singletrace = list()
                    for row in traceread:
                        # Exclude commentaries
                        if (str(row[0])[0:1] != '#'):
                            singletrace.append((float(row[0]), float(row[1])))
                    singletrace = np.array(singletrace)
                    thistrace.append(singletrace)
                    del traceread
                    del singletrace
                    tracefile.close()
            if len(thistrace) == 1:
                Trace.append(thistrace[0])
            elif len(thistrace) == 2:
                Trace.append(thistrace)
            else:
                Trace.append(None)
    else:
        # We are not importing from a session but from a zip file with
        # probably a mix of all filetypes we know. This works 
        # recursively (e.g. a zip file in a zipfile).
        allfiles = Arc.namelist()
        # Extract data to temporary folder
        tempdir = tempfile.mkdtemp()
        rmdirs = list()
        for afile in allfiles:
            apath = Arc.extract(afile, path=tempdir)
            if os.path.isdir(apath):
                rmdirs.append(apath)
                continue
            ReturnValue = openAny(tempdir, afile)
            if ReturnValue is not None:
                Correlations += ReturnValue["Correlation"]
                Trace += ReturnValue["Trace"]
                Curvelist += ReturnValue["Type"]
                fnames = ReturnValue["Filename"]
                Filelist += [ filename+"/"+fs for fs in fnames ]
            # Delte file
            try:
                os.remove(os.path.join(tempdir, afile))
            except:
                warnings.warn("{}".format(sys.exc_info()[1]))
        for rmd in rmdirs:
            try:
                os.removedirs(rmd)
            except:
                    warnings.warn("{}".format(sys.exc_info()[1]))
        try:
            os.removedirs(tempdir)
        except:
                warnings.warn("{}".format(sys.exc_info()[1]))
    Arc.close()
    dictionary = dict()
    dictionary["Correlation"] = Correlations
    dictionary["Trace"] = Trace
    dictionary["Type"] = Curvelist
    dictionary["Filename"] = Filelist
    return dictionary


# The string that is shown when opening all supported files
# We add an empty space so it is listed first in the dialogs.
Allsupfilesstring = " All supported files"

# Dictionary with filetypes that we can open
# The wildcards point to the appropriate functions.
Filetypes = { "Correlator.com (*.SIN)|*.SIN;*.sin" : openSIN,
              "ALV (*.ASC)|*.ASC;*.asc" : openASC,
              "PyCorrFit (*.csv)|*.csv" : openCSV,
              "Matlab 'Ries (*.mat)|*.mat" : openMAT,
              "PicoQuant (*.pt3)|*.pt3" : openPT3,
              "Zeiss ConfoCor3 (*.fcs)|*.fcs" : openFCS,
              "Zip file (*.zip)|*.zip" : openZIP,
              "PyCorrFit session (*.pcfs)|*.pcfs" : openZIP
            }
# For user comfort, add "All supported files" wildcard:
Filetypes = AddAllWildcard(Filetypes)


# Dictionary with filetypes we can open that have intensity traces in them.
BGFiletypes = { "Correlator.com (*.SIN)|*.SIN;*.sin" : openSIN,
                "ALV (*.ASC)|*.ASC" : openASC,
                "PyCorrFit (*.csv)|*.csv" : openCSV,
                "PicoQuant (*.pt3)|*.pt3" : openPT3,
                "Zeiss ConfoCor3 (*.fcs)|*.fcs" : openFCS,
                "Zip file (*.zip)|*.zip" : openZIP,
                "PyCorrFit session (*.pcfs)|*.pcfs" : openZIP
              }
BGFiletypes = AddAllWildcard(BGFiletypes)

