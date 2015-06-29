# -*- coding: utf-8 -*-
"""
methods to open Confocor .fcs files
"""
import os
import csv
import numpy as np
import warnings


def openFCS(dirname, filename):
    """ 
        Load data from Zeiss Confocor3
        Data is imported sequenially from the file.
        PyCorrFit will give each curve an id which corresponds to the 
        position of the curve in the .fcs file.
        
        The AIM software can save data as multiple or single data files.
        The type is identified by the first line of the .fcs file.
        
        This works with files from the Confocor2, Confocor3 (AIM) and 
        files created from the newer ZEN Software.
        
        This function is a wrapper combining *openFCS_Single* and
        *openFCS_Multiple* 
    """
    openfile = open(os.path.join(dirname, filename), 'r')
    identitystring = openfile.readline().strip()[:20]
    openfile.close()
    if identitystring == "Carl Zeiss ConfoCor3":
        return openFCS_Multiple(dirname, filename)
    else:
        return openFCS_Single(dirname, filename)


def openFCS_Multiple(dirname, filename):
    """ Load data from Zeiss Confocor3
        Data is imported sequenially from the file.
        PyCorrFit will give each curve an id which corresponds to the 
        position of the curve in the .fcs file.

        This works with files from the Confocor2, Confocor3 (AIM) and 
        files created from the newer ZEN Software.
    """
    ### TODO:
    # match curves with their timestamp
    # (actimelist and cctimelist)
    #
    openfile = open(os.path.join(dirname, filename), 'r')
    Alldata = openfile.readlines()
    # Start progressing through the file. i is the line index.
    # We are searching for "FcsDataSet" sections that contain
    # all the information we want.
    # index i for linenumber
    i = 0
    # A parameter to check whether we are in a "FcsDataSet" section
    # and should import something
    fcsset = False
    # The names of the traces
    aclist = list()     # All autocorrelation functions
    cclist = list()     # All cross-correlation functions
    # The intensity traces
    traces = list()
    # we use "AcquisitionTime" to match up curves
    thistime = None
    actimelist = list()
    cctimelist = list()
    # The correlation curves
    ac_correlations = list()
    cc_correlations = list()
    while i <= len(Alldata)-1:
        if Alldata[i].count("FcsDataSet") == 1:
            # We are in a "FcsDataSet" section
            fcsset = True
            gottrace = False
        if fcsset == True:
            if Alldata[i].partition("=")[0].strip() == "AcquisitionTime":
                thistime = Alldata[i].partition("=")[2].strip()
            if Alldata[i].partition("=")[0].strip() == "Channel":
                # Find out what type of correlation curve we have.
                # Might be interesting to the user.
                FCStype = Alldata[i].partition("=")[2].strip()
                FoundType = False
                for chnum in np.arange(4)+1:
                    if FCStype == "Auto-correlation detector "+str(chnum):
                        FoundType = "AC"+str(chnum)
                        aclist.append(FoundType)
                    elif FCStype == "Auto-correlation detector Meta"+str(chnum):
                        FoundType = "AC"+str(chnum)
                        aclist.append(FoundType)
                    else:
                        for ch2num in np.arange(4)+1:
                            if FCStype == "Cross-correlation detector "+\
                                          str(chnum)+" versus detector "+\
                                          str(ch2num):
                                FoundType = "CC"+str(chnum)+str(ch2num)
                                cclist.append(FoundType)
                            elif FCStype == "Cross-correlation detector Meta"+\
                                          str(chnum)+" versus detector Meta"+\
                                          str(ch2num):
                                FoundType = "CC"+str(chnum)+str(ch2num)
                                cclist.append(FoundType)
                if FoundType is False:
                    # Jump out of this set. We will continue at 
                    # the next "FcsDataSet"-section.
                    print "Unknown channel configuration in .fcs file: "+FCStype
                    fcsset = False
                elif FoundType[:2] == "CC":
                    cctimelist.append(thistime)
                elif FoundType[:2] == "AC":
                    actimelist.append(thistime)

            if Alldata[i].partition("=")[0].strip() == "CountRateArray":
                # Start importing the trace. This is a little difficult, since
                # traces in those files are usually very large. We will bin
                # the trace and import a lighter version of it.
                tracelength = \
                     int(Alldata[i].partition("=")[2].strip().partition(" ")[0])
                if tracelength != 0:
                    tracedata = Alldata.__getslice__(i+1, i+tracelength+1)
                    # Jump foward in the index
                    i = i + tracelength
                    readtrace = csv.reader(tracedata, delimiter='\t')
                    trace = list()
                    for row in readtrace:
                        # tau in ms, trace in kHz
                        # So we need to put some factors here
                        trace.append( (np.float(row[3])*1000,
                                       np.float(row[4])/1000) )
                    trace = np.array(trace)
                    # The trace is too big. Wee need to bin it.
                    if len(trace) >= 500:
                        # We want about 500 bins
                        # We need to sum over intervals of length *teiler*
                        teiler = int(len(trace)/500)
                        newlength = len(trace)/teiler
                        newsignal = np.zeros(newlength)
                        # Simultaneously sum over all intervals
                        for j in np.arange(teiler):
                            newsignal = \
                                 newsignal+trace[j:newlength*teiler:teiler][:,1]
                        newsignal = 1.* newsignal / teiler
                        newtimes = trace[teiler-1:newlength*teiler:teiler][:,0]
                        if len(trace)%teiler != 0:
                            # We have a rest signal
                            # We average it and add it to the trace
                            rest = trace[newlength*teiler:][:,1]
                            lrest = len(rest)
                            rest = np.array([sum(rest)/lrest])
                            newsignal = np.concatenate((newsignal, rest),
                                                       axis=0)
                            timerest = np.array([trace[-1][0]])
                            newtimes = np.concatenate((newtimes, timerest),
                                                      axis=0)
                        newtrace=np.zeros((len(newtimes),2))
                        newtrace[:,0] = newtimes
                        newtrace[:,1] = newsignal
                    else:
                        # Declare newtrace -
                        # otherwise we have a problem down three lines ;)
                        newtrace = trace
                    # Finally add the trace to the list
                    traces.append(newtrace)
                    if FoundType[:2] != "AC":
                        # For every trace there is an entry in aclist
                        print "Trace data saved in CC section."+ \
                              "I cannot handle that."
                    gottrace = True
            if Alldata[i].partition("=")[0].strip() == "CorrelationArraySize":
                # Get the correlation information
                corrlength = int(Alldata[i].partition("=")[2].strip())
                if corrlength !=0:
                    # For cross correlation or something sometimes
                    # there is no trace information.
                    if gottrace == False and FoundType[:2] =="AC":
                        # We think we know that there is no trace in CC curves
                        traces.append(None)
                    corrdata = Alldata.__getslice__(i+2, i+corrlength+2)
                    # Jump foward
                    i = i + corrlength
                    readcorr = csv.reader(corrdata, delimiter='\t')
                    corr = list()
                    for row in readcorr:
                        # tau in ms, corr-function
                        corr.append( (np.float(row[3])*1000,
                                      np.float(row[4])-1)    )
                    if FoundType[:2] == "AC":
                        ac_correlations.append(np.array(corr))
                    elif FoundType[:2] == "CC":
                        cc_correlations.append(np.array(corr))
                else:
                    # There is no correlation data in the file
                    # Fill in some dummy data. These will be removed.
                    if FoundType[:2] == "AC":
                        # append a dummy correlation curve
                        ac_correlations.append(None)
                        if gottrace == False:
                            # append a dummy trace
                            traces.append(None)
                    elif FoundType[:2] == "CC":
                        # append a dummy correlation curve
                        # cc_correlations do not have traces
                        cc_correlations.append(None)
                # We reached the end of this "FcsDataSet" section.
                fcsset = False
        i = i + 1
    # finished.
    openfile.close()
    # We now have:
    #  aclist: a list of AC curve names mentioned in the file.
    #  cclist: a list of CC curve names mentioned in the file.
    #  traces: All traces corresponding to non-"None"-type entries in
    #          ac_correlations. Not in cc_correlations,
    #          because cross-correlations are not saved with traces.?
    #
    # Identifiers:
    #  actimelist: aquisition times according to aclist
    #  cctimelist: aquisition times according to cclist
    #
    # Correlations:
    #  ac_correlations: AC-correlation data in list.
    #  cc_correlations: CC-correlation data in list.
    # 
    # ac_correlations or cc_correlations can have items that are "None".
    # These item come from averaging inside the Confocor software and
    # do not contain any data.
    # These "None" type items should be at the end of these lists.
    # If the user created .fcs files with averages between the curves,
    # the *traces* contains *None* values at those positions.
    ## We now create:
    #  curvelist: All actually used data
    #  tracelist: Traces brought into right form (also for CCs)
    #  corrlist: Correlation curves
    #  Index in curvelist defines index in trace and correlation.
    curvelist = list()
    tracelist = list()
    corrlist = list()
    
    # match up curves with their timestamps
    # (actimelist and cctimelist)
    knowntimes = list()
    for tid in actimelist:
        if tid not in knowntimes:
            knowntimes.append(tid)
            #n = actimelist.count(tid)
            actids = np.where(np.array(actimelist) == tid)[0]
            cctids = np.where(np.array(cctimelist) == tid)[0]
            
            if len(actids) == 0:
                warnings.warn("File {} timepoint {} has no AC data.".
                              format(filename, tid))
            elif len(actids) == 1:
                # single AC curve
                if ac_correlations[actids[0]] is not None:
                    curvelist.append(aclist[actids[0]])
                    tracelist.append(1*traces[actids[0]])
                    corrlist.append(ac_correlations[actids[0]])
                else:
                    if traces[actids[0]] is not None:
                        warnings.warn("File {} curve {} does not contain AC data.".format(filename, tid))
            elif len(actids) == 2:
                # Get AC data
                if aclist[actids[0]] == "AC1":
                    acdat1 = ac_correlations[actids[0]]
                    trace1 = traces[actids[0]]
                    acdat2 = ac_correlations[actids[1]]
                    trace2 = traces[actids[1]]
                elif aclist[actids[0]] == "AC2":
                    acdat1 = ac_correlations[actids[1]]
                    trace1 = traces[actids[1]]
                    acdat2 = ac_correlations[actids[0]]
                    trace2 = traces[actids[0]]
                else:
                    warnings.warn("File {} curve {}: unknown AC data.".format(filename, tid))
                    continue
                
                if acdat1 is not None:
                    #AC1
                    curvelist.append("AC1")
                    tracelist.append(trace1)
                    corrlist.append(acdat1)
                if acdat2 is not None:
                    #AC2
                    curvelist.append("AC2")
                    tracelist.append(trace2)
                    corrlist.append(acdat2)
                    
                if len(cctids) == 2:
                    # Get CC data
                    if cclist[cctids[0]] == "CC12":
                        ccdat12 = cc_correlations[cctids[0]]
                        ccdat21 = cc_correlations[cctids[1]]
                    elif cclist[cctids[0]] == "CC21":
                        ccdat12 = cc_correlations[cctids[1]]
                        ccdat21 = cc_correlations[cctids[0]]
                    else:
                        warnings.warn("File {} curve {}: unknown CC data.".format(filename, tid))
                        continue
                        
                    tracecc = [trace1, trace2]
                    if ccdat12 is not None:
                        #CC12
                        curvelist.append("CC12")
                        tracelist.append(tracecc)
                        corrlist.append(ccdat12)
                    if ccdat21 is not None:
                        #CC21
                        curvelist.append("CC21")
                        tracelist.append(tracecc)
                        corrlist.append(ccdat21)

    dictionary = dict()
    dictionary["Correlation"] = corrlist
    dictionary["Trace"] = tracelist
    dictionary["Type"] = curvelist
    filelist = list()
    for i in curvelist:
        filelist.append(filename)
    dictionary["Filename"] = filelist
    return dictionary


def openFCS_Single(dirname, filename):
    """ 
        Load data from Zeiss Confocor3 files containing only one curve.
    
        This works with files from the Confocor2, Confocor3 (AIM) and 
        files created from the newer ZEN Software.
    """
    openfile = open(os.path.join(dirname, filename), 'r')
    Alldata = openfile.readlines()
    # Start progressing through the file. i is the line index.
    # We are searching for "FcsDataSet" sections that contain
    # all the information we want.
    # index i for linenumber
    i = 0
    # Indicates if trace or FCS curve should be imported in loop
    fcscurve = False
    tracecurve = False
    while i <= len(Alldata)-1:
        if Alldata[i].partition("=")[0].strip() == "##DATA TYPE":
            # Find out what type of correlation curve we have.
            # Might be interesting to the user.
            Type  = Alldata[i].partition("=")[2].strip()
            if Type == "FCS Correlogram":
                fcscurve = True
                tracecurve = False
            elif Type == "FCS Count Rates":
                tracecurve = True
                fcscurve = False
            else:
                raise SyntaxError("Unknown file syntax: "+Type)
        i = i + 1
        if tracecurve == True:
            if Alldata[i].partition("=")[0].strip() == "##NPOINTS":
                # Start importing the trace. This is a little difficult, since
                # traces in those files are usually very large. We will bin
                # the trace and import a lighter version of it.
                tracelength = int(Alldata[i].partition("=")[2].strip())
                # Trace starts 3 lines after this.
                i = i + 3
                if tracelength != 0:
                    tracedata = Alldata.__getslice__(i, i+tracelength)
                    # Jump foward in the index
                    i = i + tracelength
                    readtrace = csv.reader(tracedata, delimiter=',')
                    trace = list()
                    for row in readtrace:
                        # tau in ms, trace in kHz
                        # So we need to put some factors here
                        trace.append( (np.float(row[0])*1000, np.float(row[1])) )
                    trace = np.array(trace)
                    # The trace is too big. Wee need to bin it.
                    if len(trace) >= 500:
                        # We want about 500 bins
                        # We need to sum over intervals of length *teiler*
                        teiler = int(len(trace)/500)
                        newlength = len(trace)/teiler
                        newsignal = np.zeros(newlength)
                        # Simultaneously sum over all intervals
                        for j in np.arange(teiler):
                            newsignal = \
                                 newsignal+trace[j:newlength*teiler:teiler][:,1]
                        newsignal = 1.* newsignal / teiler
                        newtimes = trace[teiler-1:newlength*teiler:teiler][:,0]
                        if len(trace)%teiler != 0:
                            # We have a rest signal
                            # We average it and add it to the trace
                            rest = trace[newlength*teiler:][:,1]
                            lrest = len(rest)
                            rest = np.array([sum(rest)/lrest])
                            newsignal = np.concatenate((newsignal, rest),
                                                       axis=0)
                            timerest = np.array([trace[-1][0]])
                            newtimes = np.concatenate((newtimes, timerest),
                                                      axis=0)
                        newtrace=np.zeros((len(newtimes),2))
                        newtrace[:,0] = newtimes
                        newtrace[:,1] = newsignal
                    else:
                        # Declare newtrace -
                        # otherwise we have a problem down three lines ;)
                        newtrace = trace
                tracecurve = False
        if fcscurve == True:
            if Alldata[i].partition("=")[0].strip() == "##NPOINTS":
                # Get the correlation information
                corrlength = int(Alldata[i].partition("=")[2].strip())
                i = i + 2
                if corrlength !=0:
                    corrdata = Alldata.__getslice__(i, i+corrlength)
                    # Jump foward
                    i = i + corrlength
                    readcorr = csv.reader(corrdata, delimiter=',')
                    corr = list()
                    for row in readcorr:
                        # tau in ms, corr-function
                        corr.append( (np.float(row[0]), np.float(row[1])-1) )
                    corr = np.array(corr)
                fcscurve = False
                
    # Check for correlation at lag-time zero, which lead to a bug (#64)
    # on mac OSx and potentially affects fitting.
    if corr[0][0] == 0:
        corr = corr[1:]
    openfile.close()
    dictionary = dict()
    dictionary["Correlation"] = [corr]
    dictionary["Trace"] = [newtrace]
    dictionary["Type"] = [""]
    dictionary["Filename"] = [filename]
    return dictionary
