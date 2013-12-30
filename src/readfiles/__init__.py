# -*- coding: utf-8 -*-
""" 
    PyCorrFit
    
    Module readfiles:
    Import correlation data from data files.

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
# imported by PyCorrFit.

import csv
import numpy as np
import os
import tempfile
import yaml
import zipfile

# To add a filetype add it here and in the
# dictionaries at the end of this file.
from read_ASC_ALV_6000 import openASC
from read_CSV_PyCorrFit import openCSV
from read_SIN_correlator_com import openSIN
from read_FCS_Confocor3 import openFCS
from read_mat_ries import openMAT


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
                if string[-3:] == wildcard:
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
                if string[-3:] == wildcard:
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
    fcsfitwildcard = ".fcsfit-session.zip"
    if len(filename)>19 and filename[-19:] == fcsfitwildcard:
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
            tau = list()
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
        for afile in allfiles:
            Arc.extract(afile, path=tempdir)
            ReturnValue = openAny(tempdir, afile)
            if ReturnValue is not None:
                cs = ReturnValue["Correlation"]
                ts = ReturnValue["Trace"]
                ls = ReturnValue["Type"]
                fs = ReturnValue["Filename"]
                for i in np.arange(len(cs)):
                    Correlations.append(cs[i])
                    Trace.append(ts[i])
                    Curvelist.append(ls[i])
                    Filelist.append(filename+"/"+fs[i])
            # Delte file
            os.remove(os.path.join(tempdir,afile))
        os.removedirs(tempdir)
    Arc.close()
    dictionary = dict()
    dictionary["Correlation"] = Correlations
    dictionary["Trace"] = Trace
    dictionary["Type"] = Curvelist
    dictionary["Filename"] = Filelist
    return dictionary


# The string that is shown when opening all supported files
Allsupfilesstring = "All supported files"

# Dictionary with filetypes that we can open
# The wildcards point to the appropriate functions.
Filetypes = { "Correlator.com (*.SIN)|*.SIN;*.sin" : openSIN,
              "Correlator ALV-6000 (*.ASC)|*.ASC" : openASC,
              "PyCorrFit (*.csv)|*.csv" : openCSV,
              "Matlab 'Ries (*.mat)|*.mat" : openMAT,
              "Confocor3 (*.fcs)|*.fcs" : openFCS,
              "zip files (*.zip)|*.zip" : openZIP
            }
# For user comfort, add "All supported files" wildcard:
Filetypes = AddAllWildcard(Filetypes)


# Dictionary with filetypes we can open that have intensity traces in them.
BGFiletypes = { "Correlator.com (*.SIN)|*.SIN;*.sin" : openSIN,
                "Correlator ALV-6000 (*.ASC)|*.ASC" : openASC,
                "PyCorrFit (*.csv)|*.csv" : openCSV,
                "Confocor3 (*.fcs)|*.fcs" : openFCS,
                "zip files (*.zip)|*.zip" : openZIP
              }
BGFiletypes = AddAllWildcard(BGFiletypes)
