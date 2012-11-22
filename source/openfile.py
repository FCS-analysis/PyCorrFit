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
import shutil
import sys
import tempfile
import traceback
import wx
import yaml
import zipfile

# PyCorrFit Models
import doc
import models as mdls
from tools import info

# This contains all the information necessary to import data files:
from readfiles import Filetypes
from readfiles import BGFiletypes

import platform





def ImportParametersYaml(parent, dirname):
    """ Import the parameters from a parameters.yaml file
        from an PyCorrFit session.
    """
    dlg = wx.FileDialog(parent, "Choose a session file", dirname, "", 
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
    """
    fcsfitwildcard = ".fcsfit-session.zip"
    if sessionfile is None:
        dlg = wx.FileDialog(parent, "Choose a session file", dirname, "", 
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
            return None, None, None, None, None, None, None, dirname, None
    else:
        (dirname, filename) = os.path.split(sessionfile)
        if filename[-19:] != fcsfitwildcard:
            # User specified wrong file
            print "Unknown file extension: "+filename
            # stop this function
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            return None, None, None, None, None, None, None, dirname, None

    Arc = zipfile.ZipFile(os.path.join(dirname, filename), mode='r')
    # Get the yaml parms dump:
    yamlfile = Arc.open("Parameters.yaml")
    # Parms: Fitting and drawing parameters of correlation curve
    # The *yamlfile* is responsible for the order of the Pages #i.
    Parms = yaml.safe_load(yamlfile)
    yamlfile.close()
    ## Preferences: Reserved for a future version of PyCorrFit :)
    prefname = "Preferences.yaml"
    try:
        Arc.getinfo(prefname)
    except KeyError:
        Preferences = None    
    else:
        yamlpref = Arc.open(prefname)
        Preferences = yaml.safe_load(yamlpref)
        yamlpref.close()
    # Get external functions
    ExternalFunctions = dict()
    key = 7001
    while key <= 7999:
        # (There should not be more than 1000 function)
        funcfilename = "model_"+str(key)+".txt"
        try:
            Arc.getinfo(funcfilename)
        except KeyError:
            # No more functions to import
            key = 8000
        else:
            funcfile =  Arc.open(funcfilename)
            ExternalFunctions[key] = funcfile.read()
            funcfile.close()
            key=key+1
    # Get the correlation arrays
    Array = list()
    for i in np.arange(len(Parms)):
        # The *number* is used to identify the correct file
        number = str(Parms[i][0])
        expfilename = "data"+number[1:len(number)-2]+".csv"
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
        Array.append([tau, dataexp])
        del readdata
        expfile.close()
    # Get the Traces
    Trace = list()
    for i in np.arange(len(Parms)):
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
        else:
            # Cross correlation uses two traces
            tracefilenames = ["trace"+number[1:len(number)-2]+"A.csv",
                              "trace"+number[1:len(number)-2]+"B.csv" ]
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
            Trace.append(thistrace)
        else:
            Trace.append(None)
    # Get the comments, if they exist
    commentfilename = "comments.txt"
    try:
        # Raises KeyError, if file is not present:
        Arc.getinfo(commentfilename)
    except KeyError:
        Comments = None    
    else:
        # Open the file
        commentfile = Arc.open(commentfilename, 'r')
        Comments = list()
        for i in np.arange(len(Parms)):
            # Strip line ending characters for all the Pages.
            Comments.append(commentfile.readline().strip())
        # Now Add the Session Comment (the rest of the file). 
        ComList = commentfile.readlines()
        Com = ''
        for line in ComList:
            Com = Com+line
        Comments.append(Com.strip())
        commentfile.close()
    # Get the Backgroundtraces and data if they exist
    bgfilename = "backgrounds.csv"
    try:
        # Raises KeyError, if file is not present:
        Arc.getinfo(bgfilename)
    except KeyError:
        Background = list()
    else:
        # Open the file
        Background = list()
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
                    bgtrace.append((float(row[0]), float(row[1])))
            bgtrace = np.array(bgtrace)
            
            Background.append([float(bgrow[0]), str(bgrow[1]), bgtrace])
            i = i + 1
        bgfile.close()
    Arc.close()
    return Parms, Array, Trace, Background, Preferences, Comments, \
           ExternalFunctions, dirname, filename



def saveCSV(parent, dirname, Page):
    """ Write relevant data into a comma separated list.
        
        Parameters:
        *parent*   the parent window
        *dirname* directory to set on saving
        *Page*     Page containing all necessary variables
    """
    filename = Page.tabtitle.GetValue().strip()+Page.counter[:2]
    dlg = wx.FileDialog(parent, "Choose a data file", dirname, filename, 
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
            res = exp - corr
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


def SaveSession(parent, dirname, Parms, Array, Trace, Background, Preferences,
                Comments, ExternalFunctions):
    """ Write whole Session into a zip file.
        Internal Functions:
        *Parms* of all functions will be saved in one *.yaml file.
        *Array* includes all the arrays (tau and dataexp). For each
         Page/Function those will be saved in a separate file.
        *Trace* is a list of intensity traces.
        *Background* is a list of backgrounds and their traces
        *Preferences* are not yet used
        *Comments* on the session and on each page
        We will also write a Readme.txt
    """
    dlg = wx.FileDialog(parent, "Choose a data file", dirname, "",
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
        # Parameters have to be floats in lists in order for yaml.safe_load to work        
        for idparm in np.arange(len(Parms)):
            Parms[idparm][2] = np.array(Parms[idparm][2], dtype="float").tolist()
        yaml.dump( Parms,
                     open(parmsfilename, "wb") )
        Arc.write(parmsfilename)
        # Save external functions
        for key in ExternalFunctions.keys():
            funcfilename = "model_"+str(key)+".txt"
            funcfile =  open(funcfilename, 'wb')
            funcfile.write(ExternalFunctions[key])
            funcfile.close()
            Arc.write(funcfilename)
        # Save (dataexp and tau)s into separate csv files.
        for i in np.arange(len(Array)):
            # Since *Array* and *Parms* are in the same order, which is the
            # Page order, we will identify the filename by the Page title number.
            number = str(Parms[i][0])
            expfilename = "data"+number[1:len(number)-2]+".csv"
            expfile = open(expfilename, 'wb')
            tau = Array[i][0]
            exp = Array[i][1]
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
        # Save traces into separate csv files.
        for i in np.arange(len(Trace)):
            # Since *Trace* and *Parms* are in the same order, which is the
            # Page order, we will identify the filename by the Page title number.
            if Trace[i] is not None:
                number = str(Parms[i][0])
                if Parms[i][7] is True:
                    # We have cross correlation: save two traces
                    ## A
                    tracefilenamea = "trace"+number[1:len(number)-2]+"A.csv"
                    tracefile = open(tracefilenamea, 'wb')
                    traceWriter = csv.writer(tracefile, delimiter=',')
                    time = Trace[i][0][:,0]
                    rate = Trace[i][0][:,1]
                    # Names of Columns
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
                    tracefile.close()
                    # Add to archive
                    Arc.write(tracefilenamea)
                    ## B
                    tracefilenameb = "trace"+number[1:len(number)-2]+"B.csv"
                    tracefile = open(tracefilenameb, 'wb')
                    traceWriter = csv.writer(tracefile, delimiter=',')
                    time = Trace[i][1][:,0]
                    rate = Trace[i][1][:,1]
                    # Names of Columns
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
                    tracefile.close()
                    # Add to archive
                    Arc.write(tracefilenameb)
                else:
                    # Save one single trace
                    tracefilename = "trace"+number[1:len(number)-2]+".csv"
                    tracefile = open(tracefilename, 'wb')
                    traceWriter = csv.writer(tracefile, delimiter=',')
                    time = Trace[i][:,0]
                    rate = Trace[i][:,1]
                    # Names of Columns
                    traceWriter.writerow(['# time'+' \t', 'count rate'])
                    # Actual Data
                    for j in np.arange(len(time)):
                        traceWriter.writerow([str(time[j])+" \t", str(rate[j])])
                    tracefile.close()
                    # Add to archive
                    Arc.write(tracefilename)
        # Save comments into txt file
        commentfilename = "comments.txt"
        commentfile = open(commentfilename, 'wb')
        # Comments[-1] is comment on whole Session
        for i in np.arange(len(Comments)):
            commentfile.write(Comments[i]+"\r\n")
        commentfile.close()
        Arc.write(commentfilename)
        ## Save Background information:
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
            bgfile.close()
            Arc.write(bgfilename)
        ## Readme
        rmfilename = "Readme.txt"
        rmfile = open(rmfilename, 'wb')
        rmfile.write(doc.SessionReadme(parent))
        rmfile.close()
        Arc.write(rmfilename)
        # Close the archive
        Arc.close()
        # Move archive to destination directory
        shutil.move(os.path.join(tempdir, filename), 
                    os.path.join(dirname, filename) )
        # Go to destination directory
        os.chdir(returnWD)
        # Clean up behind us
        os.remove(os.path.join(tempdir, parmsfilename))
        os.remove(os.path.join(tempdir, commentfilename))
        os.remove(os.path.join(tempdir, rmfilename))
        for key in ExternalFunctions.keys():
            funcfilename = "model_"+str(key)+".txt"
            os.remove(os.path.join(tempdir, funcfilename))
        for i in np.arange(len(Array)):
            number = str(Parms[i][0])
            expfilename = "data"+number[1:len(number)-2]+".csv"
            os.remove(os.path.join(tempdir, expfilename))
            if Trace[i] is not None:
                if Parms[i][7] is True:
                    tracefilenamea = "trace"+number[1:len(number)-2]+"A.csv"
                    os.remove(os.path.join(tempdir, tracefilenamea))
                    tracefilenameb = "trace"+number[1:len(number)-2]+"B.csv"
                    os.remove(os.path.join(tempdir, tracefilenameb))
                else:
                    tracefilename = "trace"+number[1:len(number)-2]+".csv"
                    os.remove(os.path.join(tempdir, tracefilename))
        if len(Background) > 0:
            os.remove(os.path.join(tempdir, bgfilename))
            for i in np.arange(len(Background)):
                bgtracefilename = "bg_trace"+str(i)+".csv"
                os.remove(os.path.join(tempdir, bgtracefilename))
        os.rmdir(tempdir)
        return dirname, filename
    else:
        dirname = dlg.GetDirectory()
        dlg.Destroy()
        return dirname, None


