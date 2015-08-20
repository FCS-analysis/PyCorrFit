# -*- coding: utf-8 -*-
"""
PyCorrFit - Module openfile

This file contains definitions for opening PyCorrFit sessions and
saving PyCorrFit correlation curves.
"""

import codecs
import csv
import numpy as np
import os
import shutil
import tempfile
import yaml
import zipfile
import warnings

from . import doc

# These imports are required for loading data
from .readfiles import Filetypes  # @UnusedImport
from .readfiles import BGFiletypes  # @UnusedImport
from .fcs_data_set import Trace


def LoadSessionData(sessionfile, parameters_only=False):
    """ Load PyCorrFit session data from a zip file (.pcfs)


    Parameters
    ----------
    sessionfile : str
        File from which data will be loaded
    parameters_only : bool
        Only load the parameters from the YAML file
    
    
    Returns
    -------
    Infodict : dict
        Infodict may contain the following keys:
        "Backgrounds", list: contains the backgrounds
        "Comments", dict: "Session" comment and int keys to Page titles
        "Correlations", dict: page numbers, all correlation curves
        "External Functions", dict: modelids to external model functions
        "External Weights", dict: page numbers, external weights for fitting
        "Parameters", dict: page numbers, all parameters of the pages
        "Preferences", dict: not used yet
        "Traces", dict: page numbers, all traces of the pages
        "Version", str: the PyCorrFit version of the session
    """
    Infodict = dict()
    # Get the version
    Arc = zipfile.ZipFile(sessionfile, mode='r')
    readmefile = Arc.open("Readme.txt")
    # e.g. "This file was created using PyCorrFit version 0.7.6"
    Infodict["Version"] = readmefile.readline()[46:].strip()
    readmefile.close()
    # Get the yaml parms dump:
    yamlfile = Arc.open("Parameters.yaml")
    # Parameters: Fitting and drawing parameters of correlation curve
    # The *yamlfile* is responsible for the order of the Pages #i.
    Infodict["Parameters"] = yaml.safe_load(yamlfile)
    yamlfile.close()
    if parameters_only:
        Arc.close()
        return Infodict
    # Supplementary data (errors of fit)
    supname = "Supplements.yaml"
    try:
        Arc.getinfo(supname)
    except:
        pass
    else:
        supfile = Arc.open(supname)
        supdata = yaml.safe_load(supfile)
        Infodict["Supplements"] = dict()
        for idp in supdata:
            Infodict["Supplements"][idp[0]] = dict() 
            Infodict["Supplements"][idp[0]]["FitErr"] = idp[1]
            if len(idp) > 2:
                # As of version 0.7.4 we save chi2 and shared pages -global fit
                Infodict["Supplements"][idp[0]]["Chi sq"] = idp[2]
                Infodict["Supplements"][idp[0]]["Global Share"] = idp[3]
    ## Preferences: Reserved for a future version of PyCorrFit :)
    prefname = "Preferences.yaml"
    try:
        Arc.getinfo(prefname)
    except KeyError:
        pass
    else:
        yamlpref = Arc.open(prefname)
        Infodict["Preferences"] = yaml.safe_load(yamlpref)
        yamlpref.close()
    # Get external functions
    Infodict["External Functions"] = dict()
    key = 7001
    while key <= 7999:
        # (There should not be more than 1000 functions)
        funcfilename = "model_"+str(key)+".txt"
        try:
            Arc.getinfo(funcfilename)
        except KeyError:
            # No more functions to import
            key = 8000
        else:
            funcfile =  Arc.open(funcfilename)
            Infodict["External Functions"][key] = funcfile.read()
            funcfile.close()
            key=key+1
    # Get the correlation arrays
    Infodict["Correlations"] = dict()
    for i in np.arange(len(Infodict["Parameters"])):
        # The *number* is used to identify the correct file
        number = str(Infodict["Parameters"][i][0]).strip().strip(":").strip("#")
        pageid = int(number)
        expfilename = "data"+number+".csv"
        expfile = Arc.open(expfilename, 'r')
        readdata = csv.reader(expfile, delimiter=',')
        dataexp = list()
        tau = list()
        if str(readdata.next()[0]) == "# tau only":
            for row in readdata:
                # Exclude commentaries
                if (str(row[0])[0:1] != '#'):
                    tau.append(float(row[0]))
            tau = np.array(tau)
            dataexp = None
        else:
            for row in readdata:
                # Exclude commentaries
                if (str(row[0])[0:1] != '#'):
                    dataexp.append((float(row[0]), float(row[1])))
            dataexp = np.array(dataexp)
            tau = dataexp[:,0]
        Infodict["Correlations"][pageid] = [tau, dataexp]
        del readdata
        expfile.close()
    # Get the Traces
    Infodict["Traces"] = dict()
    for i in np.arange(len(Infodict["Parameters"])):
        # The *number* is used to identify the correct file
        number = str(Infodict["Parameters"][i][0]).strip().strip(":").strip("#")
        pageid = int(number)
        # Find out, if we have a cross correlation data type
        IsCross = False
        try:
            IsCross = Infodict["Parameters"][i][7]
        except IndexError:
            # No Cross correlation
            pass
        if IsCross is False:
            tracefilenames = ["trace"+number+".csv"]
        else:
            # Cross correlation uses two traces
            tracefilenames = ["trace"+number+"A.csv",
                              "trace"+number+"B.csv" ]
        thistrace = list()
        for tracefilename in tracefilenames:
            try:
                Arc.getinfo(tracefilename)
            except KeyError:
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
        if len(thistrace) != 0:
            Infodict["Traces"][pageid] = thistrace
        else:
            Infodict["Traces"][pageid] = None
    # Get the comments, if they exist
    commentfilename = "comments.txt"
    try:
        # Raises KeyError, if file is not present:
        Arc.getinfo(commentfilename)
    except KeyError:
        pass   
    else:
        # Open the file
        commentfile = Arc.open(commentfilename, 'r')
        Infodict["Comments"] = dict()
        for i in np.arange(len(Infodict["Parameters"])):
            number = str(Infodict["Parameters"][i][0]).strip().strip(":").strip("#")
            pageid = int(number)
            # Strip line ending characters for all the Pages.
            Infodict["Comments"][pageid] = commentfile.readline().strip()
        # Now Add the Session Comment (the rest of the file). 
        ComList = commentfile.readlines()
        Infodict["Comments"]["Session"] = ''
        for line in ComList:
            Infodict["Comments"]["Session"] += line
        commentfile.close()
    # Get the Backgroundtraces and data if they exist
    bgfilename = "backgrounds.csv"
    try:
        # Raises KeyError, if file is not present:
        Arc.getinfo(bgfilename)
    except KeyError:
        pass
    else:
        # Open the file
        Infodict["Backgrounds"] = list()
        bgfile = Arc.open(bgfilename, 'r')
        bgread = csv.reader(bgfile, delimiter='\t')
        i = 0
        for bgrow in bgread:
            bgtracefilename = "bg_trace"+str(i)+".csv"
            bgtracefile = Arc.open(bgtracefilename, 'r')
            bgtraceread = csv.reader(bgtracefile, delimiter=',')
            bgtrace = list()
            for row in bgtraceread:
                # Exclude commentaries
                if (str(row[0])[0:1] != '#'):
                    bgtrace.append((np.float(row[0]), np.float(row[1])))
            bgtrace = np.array(bgtrace)
            newbackground = Trace(trace=bgtrace, name=str(bgrow[1]), countrate=np.float(bgrow[0]))
            Infodict["Backgrounds"].append(newbackground)
            i = i + 1
        bgfile.close()
    # Get external weights if they exist
    WeightsFilename = "externalweights.txt"
    try:
        # Raises KeyError, if file is not present:
        Arc.getinfo(WeightsFilename)
    except:
        pass
    else:
        Wfile = Arc.open(WeightsFilename, 'r')
        Wread = csv.reader(Wfile, delimiter='\t')
        Weightsdict = dict()
        for wrow in Wread:
            Pkey = wrow[0]  # Page of weights
            pageid = int(Pkey)
            # Do not overwrite anything
            try:
                Weightsdict[pageid]
            except:
                Weightsdict[pageid] = dict()
            Nkey = wrow[1]  # Name of weights
            Wdatafilename = "externalweights_data"+Pkey+"_"+Nkey+".csv"
            Wdatafile = Arc.open(Wdatafilename, 'r')
            Wdatareader = csv.reader(Wdatafile)
            Wdata = list()
            for row in Wdatareader:
                # Exclude commentaries
                if (str(row[0])[0:1] != '#'):
                    Wdata.append(np.float(row[0]))
            Weightsdict[pageid][Nkey] = np.array(Wdata)
        Infodict["External Weights"] = Weightsdict
    Arc.close()
    return Infodict


def SaveSessionData(sessionfile, Infodict):
    """ Session PyCorrFit session data to file.
    
    
    Parameters
    ----------
    sessionfile : str
        The suffix ".pcfs" is automatically appended.
    Infodict : dict
        Infodict may contain the following keys:
        "Backgrounds", list: contains the backgrounds
        "Comments", dict: "Session" comment and int keys to Page titles
        "Correlations", dict: page numbers, all correlation curves
        "External Functions, dict": modelids to external model functions
        "External Weights", dict: page numbers, external weights for fitting
        "Parameters", dict: page numbers, all parameters of the pages
        "Preferences", dict: not used yet
        "Traces", dict: page numbers, all traces of the pages


    The version of PyCorrFit is written to Readme.txt
    """
    (dirname, filename) = os.path.split(sessionfile)
    # Sometimes you have multiple endings...
    if filename.endswith(".pcfs") is not True:
        filename += ".pcfs"
    # Change working directory
    returnWD = os.getcwd()
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    # Create zip file
    Arc = zipfile.ZipFile(filename, mode='w')
    # Only do the Yaml thing for safe operations.
    # Make the yaml dump
    parmsfilename = "Parameters.yaml"
    # Parameters have to be floats in lists
    # in order for yaml.safe_load to work.
    Parms =  Infodict["Parameters"]
    ParmsKeys = Parms.keys()
    ParmsKeys.sort()
    Parmlist = list()
    for idparm in ParmsKeys:
        # Make sure we do not accidently save arrays.
        # This would not work correctly with yaml.
        Parms[idparm][2] = np.array(Parms[idparm][2],dtype="float").tolist()
        Parms[idparm][3] = np.array(Parms[idparm][3],dtype="bool").tolist()
        # Range of fitting parameters
        Parms[idparm][9] = np.array(Parms[idparm][9],dtype="float").tolist()
        Parmlist.append(Parms[idparm])
    yaml.dump(Parmlist, open(parmsfilename, "wb"))
    Arc.write(parmsfilename)
    os.remove(os.path.join(tempdir, parmsfilename))
    # Supplementary data (errors of fit)
    errsfilename = "Supplements.yaml"
    Sups =  Infodict["Supplements"]
    SupKeys = Sups.keys()
    SupKeys.sort()
    Suplist = list()
    for idsup in SupKeys:
        error = Sups[idsup]["FitErr"]
        chi2 = Sups[idsup]["Chi sq"]
        globalshare = Sups[idsup]["Global Share"]
        Suplist.append([idsup, error, chi2, globalshare])
    yaml.dump(Suplist, open(errsfilename, "wb"))
    Arc.write(errsfilename)
    os.remove(os.path.join(tempdir, errsfilename))
    # Save external functions
    for key in Infodict["External Functions"].keys():
        funcfilename = "model_"+str(key)+".txt"
        funcfile =  codecs.open(funcfilename, 'w', encoding="utf-8")
        funcfile.write(Infodict["External Functions"][key])
        funcfile.close()
        Arc.write(funcfilename)
        os.remove(os.path.join(tempdir, funcfilename))
    # Save (dataexp and tau)s into separate csv files.
    for pageid in Infodict["Correlations"].keys():
        # Since *Array* and *Parms* are in the same order (the page order),
        # we will identify the filename by the Page title number.
        number = str(pageid)
        expfilename = "data"+number+".csv"
        expfile = open(expfilename, 'wb')
        tau = Infodict["Correlations"][pageid][0]
        exp = Infodict["Correlations"][pageid][1]
        dataWriter = csv.writer(expfile, delimiter=',')
        if exp is not None:
            # Names of Columns
            dataWriter.writerow(['# tau', 'experimental data'])
            # Actual Data
            # Do not use len(tau) instead of len(exp[:,0])) !
            # Otherwise, the experimental data will not be saved entirely,
            # if it has been cropped. Because tau might be smaller, than
            # exp[:,0] --> tau = exp[startcrop:endcrop,0]
            for j in np.arange(len(exp[:,0])):
                dataWriter.writerow(["%.20e" % exp[j,0],
                                     "%.20e" % exp[j,1]])
        else:
            # Only write tau
            dataWriter.writerow(['# tau'+' only'])
            for j in np.arange(len(tau)):
                dataWriter.writerow(["%.20e" % tau[j]])
        expfile.close()
        # Add to archive
        Arc.write(expfilename)
        os.remove(os.path.join(tempdir, expfilename))
    # Save traces into separate csv files.
    for pageid in Infodict["Traces"].keys():
        number = str(pageid)
        # Since *Trace* and *Parms* are in the same order, which is the
        # Page order, we will identify the filename by the Page title 
        # number.
        if Infodict["Traces"][pageid] is not None and len(Infodict["Traces"][pageid]) != 0:
            if Parms[pageid][7] is True:
                # We have cross correlation: save two traces
                ## A
                tracefilenamea = "trace"+number+"A.csv"
                tracefile = open(tracefilenamea, 'wb')
                traceWriter = csv.writer(tracefile, delimiter=',')
                time = Infodict["Traces"][pageid][0][:,0]
                rate = Infodict["Traces"][pageid][0][:,1]
                # Names of Columns
                traceWriter.writerow(['# time', 'count rate'])
                # Actual Data
                for j in np.arange(len(time)):
                    traceWriter.writerow(["%.20e" % time[j],
                                          "%.20e" % rate[j]])
                tracefile.close()
                # Add to archive
                Arc.write(tracefilenamea)
                os.remove(os.path.join(tempdir, tracefilenamea))
                ## B
                tracefilenameb = "trace"+number+"B.csv"
                tracefile = open(tracefilenameb, 'wb')
                traceWriter = csv.writer(tracefile, delimiter=',')
                time = Infodict["Traces"][pageid][1][:,0]
                rate = Infodict["Traces"][pageid][1][:,1]
                # Names of Columns
                traceWriter.writerow(['# time', 'count rate'])
                # Actual Data
                for j in np.arange(len(time)):
                    traceWriter.writerow(["%.20e" % time[j],
                                          "%.20e" % rate[j]])
                tracefile.close()
                # Add to archive
                Arc.write(tracefilenameb)
                os.remove(os.path.join(tempdir, tracefilenameb))
            else:
                # Save one single trace
                tracefilename = "trace"+number+".csv"
                tracefile = open(tracefilename, 'wb')
                traceWriter = csv.writer(tracefile, delimiter=',')
                time = Infodict["Traces"][pageid][0][:,0]
                rate = Infodict["Traces"][pageid][0][:,1]
                # Names of Columns
                traceWriter.writerow(['# time', 'count rate'])
                # Actual Data
                for j in np.arange(len(time)):
                    traceWriter.writerow(["%.20e" % time[j],
                                          "%.20e" % rate[j]])
                tracefile.close()
                # Add to archive
                Arc.write(tracefilename)
                os.remove(os.path.join(tempdir, tracefilename))
    # Save comments into txt file
    commentfilename = "comments.txt"
    commentfile = open(commentfilename, 'wb')
    # Comments[-1] is comment on whole Session
    Ckeys = Infodict["Comments"].keys()
    Ckeys.sort()
    for key in Ckeys:
        if key != "Session":
            commentfile.write(Infodict["Comments"][key]+"\r\n")
    commentfile.write(Infodict["Comments"]["Session"])
    commentfile.close()
    Arc.write(commentfilename)
    os.remove(os.path.join(tempdir, commentfilename))
    ## Save Background information:
    Background = Infodict["Backgrounds"]
    if len(Background) > 0:
        # We do not use a comma separated, but a tab separated file,
        # because a comma might be in the name of a bg.
        bgfilename = "backgrounds.csv"
        bgfile = open(bgfilename, 'wb')
        bgwriter = csv.writer(bgfile, delimiter='\t')
        for i in np.arange(len(Background)):
            bgwriter.writerow([str(Background[i].countrate), Background[i].name])
            # Traces
            bgtracefilename = "bg_trace"+str(i)+".csv"
            bgtracefile = open(bgtracefilename, 'wb')
            bgtraceWriter = csv.writer(bgtracefile, delimiter=',')
            bgtraceWriter.writerow(['# time', 'count rate'])
            # Actual Data
            time = Background[i][:,0]
            rate = Background[i][:,1]
            for j in np.arange(len(time)):
                bgtraceWriter.writerow(["%.20e" % time[j],
                                        "%.20e" % rate[j]])
            bgtracefile.close()
            # Add to archive
            Arc.write(bgtracefilename)
            os.remove(os.path.join(tempdir, bgtracefilename))
        bgfile.close()
        Arc.write(bgfilename)
        os.remove(os.path.join(tempdir, bgfilename))
    ## Save External Weights information
    WeightedPageID = Infodict["External Weights"].keys()
    WeightedPageID.sort()
    WeightFilename = "externalweights.txt"
    WeightFile = open(WeightFilename, 'wb')
    WeightWriter = csv.writer(WeightFile, delimiter='\t')
    for pageid in WeightedPageID:
        number = str(pageid)
        NestWeights = Infodict["External Weights"][pageid].keys()
        # The order of the types does not matter, since they are
        # sorted in the frontend and upon import. We sort them here, anyhow.
        NestWeights.sort()
        for Nkey in NestWeights:
            WeightWriter.writerow([number, str(Nkey).strip()])
            # Add data to a File
            WeightDataFilename = "externalweights_data"+number+\
                                 "_"+str(Nkey).strip()+".csv"
            WeightDataFile = open(WeightDataFilename, 'wb')
            WeightDataWriter = csv.writer(WeightDataFile)
            wdata = Infodict["External Weights"][pageid][Nkey]
            for jw in np.arange(len(wdata)):
                WeightDataWriter.writerow([str(wdata[jw])])
            WeightDataFile.close()
            Arc.write(WeightDataFilename)
            os.remove(os.path.join(tempdir, WeightDataFilename))
    WeightFile.close()
    Arc.write(WeightFilename)
    os.remove(os.path.join(tempdir, WeightFilename))
    ## Readme
    rmfilename = "Readme.txt"
    rmfile = open(rmfilename, 'wb')
    rmfile.write(ReadmeSession)
    rmfile.close()
    Arc.write(rmfilename)
    os.remove(os.path.join(tempdir, rmfilename))
    # Close the archive
    Arc.close()
    # Move archive to destination directory
    shutil.move(os.path.join(tempdir, filename), 
                os.path.join(dirname, filename) )
    # Go to destination directory
    os.chdir(returnWD)
    os.rmdir(tempdir)


def ExportCorrelation(exportfile, Page, info, savetrace=True):
    """ Write correlation data to a file
        
    
    Parameters
    ----------
    exportfile : str
        Absolute filename to save data
    Page : PyCorrFit Page object
        Contains all correlation data
    info : module
        The `info` tool module. This is a workaround until Page has
        its own class to create info data.
    savetrace : bool
        Append the trace to the file
    """

    openedfile = codecs.open(exportfile, 'w', encoding="utf-8")
    ## First, some doc text
    openedfile.write(ReadmeCSV.replace('\n', '\r\n'))
    # The infos
    InfoMan = info.InfoClass(CurPage=Page)
    PageInfo = InfoMan.GetCurFancyInfo()
    for line in PageInfo.splitlines():
        openedfile.write(u"# "+line+"\r\n")
    openedfile.write(u"#\r\n#\r\n")
    # Get all the data we need from the Page
    # Modeled data
    corr = Page.corr
    mod = corr.modeled_plot[:,1]
    if corr.correlation is not None:
        # Experimental data
        tau = corr.correlation_fit[:,0]
        exp = corr.correlation_fit[:,1]
        res = corr.residuals_fit[:,1]
        # Plotting! Because we only export plotted area.
        
        if corr.is_weighted_fit:
            weightname = corr.fit_weight_type
            try:
                weight = corr.fit_results["fit weights"]
            except KeyError:
                weight = corr.fit_weight_data
    
            if weight is None:
                pass
            
            elif len(weight) != len(exp):
                text = "Weights have not been calculated for the "+\
                       "area you want to export. Pressing 'Fit' "+\
                       "again should solve this issue. Weights will "+\
                       "not be saved."
                warnings.warn(text)
                weight = None
        else:
            weight = None
            weightname = None
    else:
        tau = corr.lag_time_fit
        exp = None
        res = None
    # Include weights in data saving:
    # PyCorrFit thinks in [ms], but we will save as [s]
    timefactor = 0.001
    tau = timefactor * tau
    ## Now we want to write all that data into the file
    # This is for csv writing:
    ## Correlation curve
    dataWriter = csv.writer(openedfile, delimiter='\t')
    if exp is not None:
        header = '# Lag time [s]'+"\t"+ \
                 'Experimental correlation'+"\t"+ \
                 'Fitted correlation'+ "\t"+ \
                 'Residuals'+"\r\n"
        data = [tau, exp, mod, res]
        if corr.is_weighted_fit and weight is not None:
            header = "{} \t Weights [{}] \r\n".format(
                      header.strip(), weightname)
            data.append(weight)
    else:
        header = '# Lag time [s]'+"\t"+ \
                 'Correlation function'+"\r\n"
        data = [tau, mod]
    # Write header
    openedfile.write(header)
    # Write data
    for i in np.arange(len(data[0])):
        # row-wise, data may have more than two elements per row
        datarow = list()
        for j in np.arange(len(data)):
            rowcoli = "{:.10e}".format(data[j][i])
            datarow.append(rowcoli)
        dataWriter.writerow(datarow)
    ## Trace
    # Only save the trace if user wants us to:
    if savetrace:
        # We will also save the trace in [s]
        # Intensity trace in kHz may stay the same
        if len(corr.traces) > 0:
            # Mark beginning of Trace
            openedfile.write('#\r\n#\r\n# BEGIN TRACE\r\n#\r\n')
            # Columns
            time = corr.traces[0][:,0]*timefactor
            intensity = corr.traces[0][:,1]
            # Write
            openedfile.write('# Time [s]'+"\t" 
                                 'Intensity trace [kHz]'+" \r\n")
            for i in np.arange(len(time)):
                dataWriter.writerow(["{:.10e}".format(time[i]),
                                     "{:.10e}".format(intensity[i])])
        if len(corr.traces) > 1:
            # We have some cross-correlation here:
            # Mark beginning of Trace B
            openedfile.write('#\r\n#\r\n# BEGIN SECOND TRACE\r\n#\r\n')
            # Columns
            time = corr.traces[1][:,0]*timefactor
            intensity = corr.traces[1][:,1]
            # Write
            openedfile.write('# Time [s]'+"\t" 
                                 'Intensity trace [kHz]'+" \r\n")
            for i in np.arange(len(time)):
                dataWriter.writerow(["{:.10e}".format(time[i]),
                                     "{:.10e}".format(intensity[i])])

        openedfile.close()


session_wildcards = [".pcfs", ".pycorrfit-session.zip"]


ReadmeCSV = """# This file was created using PyCorrFit version {}.
#
# Lines starting with a '#' are treated as comments.
# The data is stored as CSV below this comment section.
# Data usually consists of lag times (channels) and
# the corresponding correlation function - experimental
# and fitted values plus resulting residuals.
# If this file is opened by PyCorrFit, only the first two
# columns will be imported as experimental data.
#
""".format(doc.__version__)
    
    
ReadmeSession = """This file was created using PyCorrFit version {}.
The .zip archive you are looking at is a stored session of PyCorrFit.
If you are interested in how the data is stored, you will find
out here. Most important are the dimensions of units:
Dimensionless representation:
 unit of time        : 1 ms
 unit of inverse time: 10³ /s
 unit of distance    : 100 nm
 unit of Diff.coeff  : 10 µm²/s
 unit of inverse area: 100 /µm²
 unit of inv. volume : 1000 /µm³
From there, the dimension of any parameter may be
calculated.

There are a number of files within this archive, 
depending on what was done during the session.

backgrounds.csv
 - Contains the list of backgrounds used and
 - Averaged intensities in [kHz]

bg_trace*.csv (where * is an integer)
 - The trace of the background corresponding
   to the line number in backgrounds.csv
 - Time in [ms], Trace in [kHz]

comments.txt
 - Contains page titles and session comment
 - First n lines are titles, rest is session
   comment (where n is total number of pages)

data*.csv (where * is (Number of page))
 - Contains lag times [ms]
 - Contains experimental data, if available

externalweights.txt
 - Contains names (types) of external weights other than from
   Model function or spline fit
 - Linewise: 1st element is page number, 2nd is name
 - According to this data, the following files are present in the archive

externalweights_data_*PageID*_*Type*.csv
 - Contains weighting information of Page *PageID* of type *Type*

model_*ModelID*.txt
 - An external (user-defined) model file with internal ID *ModelID*

Parameters.yaml
 - Contains all Parameters for each page
   Block format:
    - - '#(Number of page): '       
      - (Internal model ID)
      - (List of parameters)
      - (List of checked parameters (for fitting))
      - [(Min channel selected), (Max channel selected)]
      - [(Weighted fit method (0=None, 1=Spline, 2=Model function)), 
         (No. of bins from left and right),
         (No. of knots (of e.g. spline)),
         (Type of fitting algorithm (e.g. "Lev-Mar", "Nelder-Mead")]
      - [B1,B2] Background to use (line in backgrounds.csv)
           B2 is always *null* for autocorrelation curves
      - Data type is Cross-correlation?
      - Parameter id (int) used for normalization in plotting.
        This number first enumerates the model parameters and then
        the supplemental parameters (e.g. "n1").
      - - [min, max] fitting parameter range of 1st parameter
        - [min, max] fitting parameter range of 2nd parameter
        - etc.
 - Order in Parameters.yaml defines order of pages in a session
 - Order in Parameters.yaml defines order in comments.txt

Readme.txt (this file)

Supplements.yaml
 - Contains errors of fitting
   Format:
   -- Page number
    -- [parameter id, error value]
     - [parameter id, error value]
    - Chi squared
    - [pages that share parameters] (from global fitting)
     
trace*.csv (where * is (Number of page) | appendix "A" or "B" point to
            the respective channels (only in cross-correlation mode))
 - Contains times [ms]
 - Contains countrates [kHz]
""".format(doc.__version__)
