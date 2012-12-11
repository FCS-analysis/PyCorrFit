# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module openfile
    This file is used to define operations on how to open some files.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


import csv
import numpy as np
import os
import platform
import shutil
import sys
import tempfile
import traceback
import wx
import yaml
import zipfile

import doc
import models as mdls
from tools import info
# This contains all the information necessary to import data files:
from readfiles import Filetypes
from readfiles import BGFiletypes


def ImportParametersYaml(parent, dirname):
    """ Import the parameters from a parameters.yaml file
        from an PyCorrFit session.
    """
    dlg = wx.FileDialog(parent, "Open session file", dirname, "", 
                                "*.fcsfit-session.zip", wx.OPEN)
    # user cannot do anything until he clicks "OK"
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetFilename()
        dirname = dlg.GetDirectory()
        dlg.Destroy()
        Arc = zipfile.ZipFile(os.path.join(dirname, filename), mode='r')
        # Get the yaml parms dump:
        yamlfile = Arc.open("Parameters.yaml")
        # Parms: Fitting and drawing parameters of correlation curve
        # The *yamlfile* is responsible for the order of the Pages #i.
        Parms = yaml.safe_load(yamlfile)
        yamlfile.close()
        Arc.close()
        return Parms, dirname, filename
    else:
        dirname=dlg.GetDirectory()
        return None, dirname, None


def OpenSession(parent, dirname, sessionfile=None):
    """ Load a whole session that has previously been saved
        by PyCorrFit.
        Infodict may contain the following keys:
        "Backgrounds", list: contains the backgrounds
        "Comments", dict: "Session" comment and int keys to Page titles
        "Correlations", dict: page numbers, all correlation curves
        "External Functions", dict: modelids to external model functions
        "External Weights", dict: page numbers, external weights for fitting
        "Parameters", dict: page numbers, all parameters of the pages
        "Preferences", dict: not used yet
        "Traces", dict: page numbers, all traces of the pages
    """
    Infodict = dict()
    fcsfitwildcard = ".fcsfit-session.zip"
    if sessionfile is None:
        dlg = wx.FileDialog(parent, "Open session file", dirname, "", 
                        "*"+fcsfitwildcard, wx.OPEN)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            dlg.Destroy()
        else:
            # User did not press OK
            # stop this function
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            return None, dirname, None
    else:
        (dirname, filename) = os.path.split(sessionfile)
        if filename[-19:] != fcsfitwildcard:
            # User specified wrong file
            print "Unknown file extension: "+filename
            # stop this function
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            return None, dirname, None
    Arc = zipfile.ZipFile(os.path.join(dirname, filename), mode='r')
    # Get the yaml parms dump:
    yamlfile = Arc.open("Parameters.yaml")
    # Parameters: Fitting and drawing parameters of correlation curve
    # The *yamlfile* is responsible for the order of the Pages #i.
    Infodict["Parameters"] = yaml.safe_load(yamlfile)
    yamlfile.close()
    # Supplementary data

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
            Infodict["Supplements"][idp[0]] = idp[1]
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
            Infodict["Backgrounds"].append([np.float(bgrow[0]), str(bgrow[1]), bgtrace])
            i = i + 1
        bgfile.close()
    # Get external weights if they exist
    Info = dict()
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
    return Infodict, dirname, filename


def saveCSV(parent, dirname, Page):
    """ Write relevant data into a comma separated list.
        
        Parameters:
        *parent*   the parent window
        *dirname* directory to set on saving
        *Page*     Page containing all necessary variables
    """
    filename = Page.tabtitle.GetValue().strip()+Page.counter[:2]
    dlg = wx.FileDialog(parent, "Save curve", dirname, filename, 
          "Correlation with trace (*.csv)|*.csv;*.CSV"+\
          "|Correlation only (*.csv)|*.csv;*.CSV",
           wx.SAVE|wx.FD_OVERWRITE_PROMPT)
    # user cannot do anything until he clicks "OK"
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetFilename()
        if filename.lower().endswith(".csv") is not True:
            filename = filename+".csv"
        dirname = dlg.GetDirectory()
        openedfile = open(os.path.join(dirname, filename), 'wb')
        ## First, some doc text
        openedfile.write(doc.saveCSVinfo(parent).replace('\n', '\r\n'))
        # The infos
        InfoMan = info.InfoClass(CurPage=Page)
        PageInfo = InfoMan.GetCurFancyInfo()
        for line in PageInfo.splitlines():
            openedfile.write("# "+line+"\r\n")
        openedfile.write("#\r\n#\r\n")
        # Get all the data we need from the Page
        # Modeled data
        corr = Page.datacorr[:,1]
        if Page.dataexp is not None:
            # Experimental data
            tau = Page.dataexp[:,0]
            exp = Page.dataexp[:,1]
            res = Page.resid[:,1]
        else:
            tau = Page.datacorr[:,0]
            exp = None
            res = None
        # PyCorrFit thinks in [ms], but we will save as [s]
        timefactor = 0.001
        tau = timefactor * tau
        ## Now we want to write all that data into the file
        # This is for csv writing:
        ## Correlation curve
        dataWriter = csv.writer(openedfile, delimiter=',')
        if exp is not None:
            # Names of Columns
            openedfile.write('# Channel (tau [s])'+" \t,"+ 
                                 'Experimental correlation'+" \t,"+
                                 'Fitted correlation'+ " \t,"+ 
                                 'Resuduals'+"\r\n")
            # Actual Data
            for i in np.arange(len(tau)):
                dataWriter.writerow([str(tau[i])+" \t", str(exp[i])+" \t", 
                                     str(corr[i])+" \t", str(res[i])])
        else:
            # Only write Correlation curve
            openedfile.write('# Channel (tau [s])'+" \t," 
                                 'Correlation function'+" \r\n")
            for i in np.arange(len(tau)):
                dataWriter.writerow([str(tau[i])+" \t", str(corr[i])])
        ## Trace
        # Only save the trace if user wants us to:
        if dlg.GetFilterIndex() == 0:
            # We will also save the trace in [s]
            # Intensity trace in kHz may stay the same
            if Page.trace is not None:
                # Mark beginning of Trace
                openedfile.write('#\r\n#\r\n# BEGIN TRACE\r\n#\r\n')
                # Columns
                time = Page.trace[:,0]*timefactor
                intensity = Page.trace[:,1]
                # Write
                openedfile.write('# Time [s]'+" \t," 
                                     'Intensity trace [kHz]'+" \r\n")
                for i in np.arange(len(time)):
                    dataWriter.writerow([str(time[i])+" \t", str(intensity[i])])
            elif Page.tracecc is not None:
                # We have some cross-correlation here:
                # Mark beginning of Trace A
                openedfile.write('#\r\n#\r\n# BEGIN TRACE\r\n#\r\n')
                # Columns
                time = Page.tracecc[0][:,0]*timefactor
                intensity = Page.tracecc[0][:,1]
                # Write
                openedfile.write('# Time [s]'+" \t," 
                                     'Intensity trace [kHz]'+" \r\n")
                for i in np.arange(len(time)):
                    dataWriter.writerow([str(time[i])+" \t", str(intensity[i])])
                # Mark beginning of Trace B
                openedfile.write('#\r\n#\r\n# BEGIN SECOND TRACE\r\n#\r\n')
                # Columns
                time = Page.tracecc[1][:,0]*timefactor
                intensity = Page.tracecc[1][:,1]
                # Write
                openedfile.write('# Time [s]'+" \t," 
                                     'Intensity trace [kHz]'+" \r\n")
                for i in np.arange(len(time)):
                    dataWriter.writerow([str(time[i])+" \t", str(intensity[i])])
        dlg.Destroy()
        openedfile.close()
        return dirname, filename
    else:
        dirname = dlg.GetDirectory()
        dlg.Destroy()
        return dirname, None


def SaveSession(parent, dirname, Infodict):
    """ Write whole Session into a zip file.
        Infodict may contain the following keys:
        "Backgrounds", list: contains the backgrounds
        "Comments", dict: "Session" comment and int keys to Page titles
        "Correlations", dict: page numbers, all correlation curves
        "External Functions, dict": modelids to external model functions
        "External Weights", dict: page numbers, external weights for fitting
        "Parameters", dict: page numbers, all parameters of the pages
        "Preferences", dict: not used yet
        "Traces", dict: page numbers, all traces of the pages
        We will also write a Readme.txt
    """
    dlg = wx.FileDialog(parent, "Save session file", dirname, "",
                     "*.fcsfit-session.zip", wx.SAVE|wx.FD_OVERWRITE_PROMPT)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetFilename()
        # Sometimes you have multiple endings...
        if filename.endswith(".fcsfit-session.zip") is not True:
            filename = filename+".fcsfit-session.zip"
        dirname = dlg.GetDirectory()
        dlg.Destroy()
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
            Parms[idparm][2] = np.array(Parms[idparm][2],dtype="float").tolist()
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
            Suplist.append([idsup,Sups[idsup]])
        yaml.dump(Suplist, open(errsfilename, "wb"))
        Arc.write(errsfilename)
        os.remove(os.path.join(tempdir, errsfilename))
        # Save external functions
        for key in Infodict["External Functions"].keys():
            funcfilename = "model_"+str(key)+".txt"
            funcfile =  open(funcfilename, 'wb')
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
                dataWriter.writerow(['# tau'+' \t', 'experimental data'])
                # Actual Data
                # Do not use len(tau) instead of len(exp[:,0])) !
                # Otherwise, the experimental data will not be saved entirely,
                # if it has been cropped. Because tau might be smaller, than
                # exp[:,0] --> tau = exp[startcrop:endcrop,0]
                for j in np.arange(len(exp[:,0])):
                    dataWriter.writerow([str(exp[j,0])+" \t", str(exp[j,1])])
            else:
                # Only write tau
                dataWriter.writerow(['# tau'+' only'])
                for j in np.arange(len(tau)):
                    dataWriter.writerow([str(tau[j])])
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
            if Infodict["Traces"][pageid] is not None:
                if Parms[pageid][7] is True:
                    # We have cross correlation: save two traces
                    ## A
                    tracefilenamea = "trace"+number+"A.csv"
                    tracefile = open(tracefilenamea, 'wb')
                    traceWriter = csv.writer(tracefile, delimiter=',')
                    time = Infodict["Traces"][pageid][0][:,0]
                    rate = Infodict["Traces"][pageid][0][:,1]
                    # Names of Columns
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
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
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
                    tracefile.close()
                    # Add to archive
                    Arc.write(tracefilenameb)
                    os.remove(os.path.join(tempdir, tracefilenameb))
                else:
                    # Save one single trace
                    tracefilename = "trace"+number+".csv"
                    tracefile = open(tracefilename, 'wb')
                    traceWriter = csv.writer(tracefile, delimiter=',')
                    time = Infodict["Traces"][pageid][:,0]
                    rate = Infodict["Traces"][pageid][:,1]
                    # Names of Columns
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
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
                bgwriter.writerow([str(Background[i][0]), Background[i][1]])
                # Traces
                bgtracefilename = "bg_trace"+str(i)+".csv"
                bgtracefile = open(bgtracefilename, 'wb')
                bgtraceWriter = csv.writer(bgtracefile, delimiter=',')
                bgtraceWriter.writerow(['# time'+' \t', 'count rate'])
                # Actual Data
                time = Background[i][2][:,0]
                rate = Background[i][2][:,1]
                for j in np.arange(len(time)):
                    bgtraceWriter.writerow([str(time[j])+" \t", str(rate[j])])
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
        rmfile.write(doc.SessionReadme(parent))
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
        return dirname, filename
    else:
        dirname = dlg.GetDirectory()
        dlg.Destroy()
        return dirname, None
