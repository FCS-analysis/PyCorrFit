# -*- coding: utf-8 -*-
""" 
    PyCorrFit
    
    functions in this file: *openASC*

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
from __future__ import division

import os
import csv
import numpy as np


def openASC(dirname, filename):
    """ Read data from a .ASC file, created by
        some ALV-6000 correlator.

            ALV-6000/E-WIN Data
            Date :	"2/20/2012"
            ...
            "Correlation"
              1.25000E-004	  3.00195E-001
              2.50000E-004	  1.13065E-001
              3.75000E-004	  7.60367E-002
              5.00000E-004	  6.29926E-002
              6.25000E-004	  5.34678E-002
              7.50000E-004	  4.11506E-002
              8.75000E-004	  4.36752E-002
              1.00000E-003	  4.63146E-002
              1.12500E-003	  3.78226E-002
            ...
              3.35544E+004	 -2.05799E-006
              3.77487E+004	  4.09032E-006
              4.19430E+004	  4.26295E-006
              4.61373E+004	  1.40265E-005
              5.03316E+004	  1.61766E-005
              5.45259E+004	  2.19541E-005
              5.87202E+004	  3.26527E-005
              6.29145E+004	  2.72920E-005

            "Count Rate"
               1.17188	      26.77194
               2.34375	      26.85045
               3.51563	      27.06382
               4.68750	      26.97932
               5.85938	      26.73694
               7.03125	      27.11332
               8.20313	      26.81376
               9.37500	      26.82741
              10.54688	      26.88801
              11.71875	      27.09710
              12.89063	      27.13209
              14.06250	      27.02200
              15.23438	      26.95287
              16.40625	      26.75657
              17.57813	      26.43056
            ...
             294.14063	      27.22597
             295.31250	      26.40581
             296.48438	      26.33497
             297.65625	      25.96457
             298.82813	      26.71902

        1. We are interested in the "Correlation" section,
        where the first column denotes tau in ms and the second row the
        correlation signal. Values are separated by a tabulator "\t" (some " ").

        2. We are also interested in the "Count Rate" section. Here the times
        are saved as seconds and not ms like above.

        3. There is some kind of mode where the ALV exports five runs at a
        time and averages them. The sole correlation data is stored in the
        file, but the trace is only stored as average or something.
        So I would not recommend this. However, I added support for this.
        PyCorrFit then only imports the average data.
         ~ Paul, 2012-02-20
        Correlation data starts at "Correlation (Multi, Averaged)".

        Returns:
        [0]:
         An array with tuples containing two elements:
         1st: tau in ms
         2nd: corresponding correlation signal
        [1]:
         Intensity trace:
         1st: time in ms
         2nd: Trace in kHz
        [2]:
         An array with N elements, indicating, how many curves we are opening
         from the file. Elements can be names and must be convertible to
         strings.
    """
    openfile = open(os.path.join(dirname, filename), 'r')
    Alldata = openfile.readlines()
    # End of trace
    EndT = Alldata.__len__()
    ## Correlation function
    # Find out where the correlation function is
    for i in np.arange(len(Alldata)):
        if Alldata[i].startswith('Mode'):
            mode = Alldata[i][5:].strip(' ":').strip().strip('"')
            if mode.lower().count('single'):
                single = True
                channel = mode.split(" ")[-1]
            else:
                # dual
                single = False
            # accc ?
            if mode.lower().count("cross") == 1:
                accc = "CC"
            else:
                accc = "AC"
        if Alldata[i].startswith('"Correlation'):
            # This tells us if there is only one curve or if there are
            # multiple curves with an average.
            if (Alldata[i].strip().lower() == 
                '"correlation (multi, averaged)"' ):
                multidata = True
            else:
                multidata = False
        if Alldata[i].startswith('"Correlation"'):
            # Start of correlation function
            StartC = i+1
        if Alldata[i].startswith('"Correlation (Multi, Averaged)"'):
            # Start of AVERAGED correlation function !!!
            # There are several curves now.
            StartC = i+2
        if Alldata[i].replace(" ", "").lower().strip() == '"countrate"':
            # takes cate of "Count Rate" and "Countrate"
            # End of correlation function
            EndC = i-1
            # Start of trace (goes until end of file)
            StartT = i+1
        if Alldata[i].startswith('Monitor Diode'):
            EndT = i-1
    # Get the header
    Namedata = Alldata.__getslice__(StartC-1, StartC)
    ## Define *curvelist*
    curvelist = csv.reader(Namedata, delimiter='\t').next()
    if len(curvelist) <= 2:
        # Then we have just one single correlation curve
        curvelist = [""]
    else:
        # We have a number of correlation curves. We need to specify
        # names for them. We take these names from the headings.
        # Lag times not in the list
        curvelist.remove(curvelist[0])
        # Last column is empty
        curvelist.remove(curvelist[-1])
    ## Correlation function
    Truedata = Alldata.__getslice__(StartC, EndC)
    readdata = csv.reader(Truedata, delimiter='\t')
    data = list()
    # Add lists to *data* according to the length of *curvelist*
    for item in curvelist:
        data.append(list())
    # Work through the rows in the read data
    for row in readdata:
        for i in np.arange(len(curvelist)):
            if len(row) > 0:
                data[i].append( (np.float(row[0]), np.float(row[i+1])) )
    ## Trace
    # Trace is stored in two columns
    # 1st column: time [s]
    # 2nd column: trace [kHz] 
    # Get the trace
    Tracedata = Alldata.__getslice__(StartT, EndT)
    timefactor = 1000 # because we want ms instead of s
    readtrace = csv.reader(Tracedata, delimiter='\t')
    trace = list()
    trace2 = list()
    # Work through the rows
    for row in readtrace:
        # time in ms, countrate
        trace.append(list())
        trace[0].append((np.float(row[0])*timefactor,
                         np.float(row[1])))
        # Only trace[0] contains the trace!
        for i in np.arange(len(curvelist)-1):
            trace.append(list())
            trace[i+1].append((np.float(row[0])*timefactor, 0))
        if not single:
            k = len(curvelist)/2
            if int(k) != k:
                print "Problem with ALV data. Single mode not recognized."
            # presumably dual mode. There is a second trace
            # time in ms, countrate
            trace2.append(list())
            trace2[0].append((np.float(row[0])*timefactor,
                              np.float(row[2])))
            # Only trace2[0] contains the trace!
            for i in np.arange(len(curvelist)-1):
                trace2.append(list())
                trace2[i+1].append((np.float(row[0])*timefactor, 0))
    # return as an array
    openfile.close()

    # group the resulting curves
    corrlist = list()
    tracelist = list()
    typelist = list()
    
        
    if single:
        # We only have several runs and one average
        # split the trace into len(curvelist)-1 equal parts
        if multidata:
            nav = 1
        else:
            nav = 0
        splittrace = mysplit(trace[0], len(curvelist)-nav)
        i = 0
        for t in range(len(curvelist)):
            typ = curvelist[t]
            if typ.lower()[:7] == "average":
                typelist.append("{} average".format(channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(np.array(trace[0]))
            else:
                typelist.append("{} {}".format(accc, channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(splittrace[i])
                i += 1
    elif accc == "AC":
        # Dual mode, autocorrelation
        # We now have two averages and two different channels.
        # We now have two traces.
        # The data is assembled in blocks. That means the first block
        # contains an average and the data of channel 0 and the second
        # block contains data and average of channel 1. We can thus
        # handle the data from 0 to len(curvelist)/2 and from
        # len(curvelist)/2 to len(curvelist) as two separate data sets.
        # CHANNEL 0
        if multidata:
            nav = 1
        else:
            nav = 0
        channel = "CH0"
        splittrace = mysplit(trace[0], len(curvelist)/2-nav)
        i = 0
        for t in range(int(len(curvelist)/2)):
            typ = curvelist[t]
            if typ.lower()[:7] == "average":
                typelist.append("{} average".format(channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(np.array(trace[0]))
            else:
                typelist.append("{} {}".format(accc, channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(splittrace[i])
                i += 1
        # CHANNEL 1
        channel = "CH1"
        splittrace2 = mysplit(trace2[0], len(curvelist)/2-nav)
        i = 0
        for t in range(int(len(curvelist)/2),int(len(curvelist))):
            typ = curvelist[t]
            if typ.lower()[:7] == "average":
                typelist.append("{} average".format(channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(np.array(trace2[0]))
            else:
                typelist.append("{} {}".format(accc, channel))
                corrlist.append(np.array(data[t]))
                tracelist.append(splittrace2[i])
                i += 1
    elif accc == "CC":
        if multidata:
            nav = 1
        else:
            nav = 0
        # Dual mode, cross-correlation
        channel = "CC01"
        splittrace = mysplit(trace[0], len(curvelist)/2-nav)
        splittrace2 = mysplit(trace2[0], len(curvelist)/2-nav)
        i = 0
        for t in range(int(len(curvelist)/2)):
            typ = curvelist[t]
            if typ.lower()[:7] == "average":
                typelist.append("{} average".format(channel))
                corrlist.append(np.array(data[t]))
                tracelist.append([np.array(trace[0]),
                                  np.array(trace2[0])  ])
            else:
                typelist.append("{} {}".format(accc, channel))
                corrlist.append(np.array(data[t]))
                tracelist.append([splittrace[i], splittrace2[i]])
                i += 1
        # CHANNEL 1
        channel = "CC10"
        i = 0
        for t in range(int(len(curvelist)/2),int(len(curvelist))):
            typ = curvelist[t]
            if typ.lower()[:7] == "average":
                typelist.append("{} average".format(channel))
                corrlist.append(np.array(data[t]))
                # order must be the same as above
                tracelist.append([np.array(trace[0]),
                                  np.array(trace2[0])  ])
            else:
                typelist.append("{} {}".format(accc, channel))
                corrlist.append(np.array(data[t]))
                # order must be the same as above
                tracelist.append([splittrace[i], splittrace2[i]])
                i += 1
    else:
        print "Could not detect data file format for: {}".format(filename)
        corrlist = np.array(data)
        tracelist = np.array(trace)
        typelist = curvelist

    dictionary = dict()
    dictionary["Correlation"] = corrlist
    dictionary["Trace"] = tracelist
    dictionary["Type"] = typelist
    filelist = list()
    for i in curvelist:
        filelist.append(filename)
    dictionary["Filename"] = filelist
    return dictionary


def mysplit(a, n):
    """
       Split a trace into n equal parts by interpolation.
       The signal average is preserved, but the signal variance will
       decrease.
    """
    if n == 1:
        return [np.array(a)]
    a = np.array(a)
    N = len(a)
    lensplit = np.int(np.ceil(N/n))

    # xp is actually rounded -> recalculate
    xp, step = np.linspace(a[:,0][0], a[:,0][-1], N,
                           endpoint=True, retstep=True)
    
    # let xp start at zero
    xp -= a[:,0][0]
    yp = a[:,1]
    
    # time frame for each new curve
    #dx = xp[-1]/n

    # perform interpolation of new trace
    x, newstep = np.linspace(0, xp[-1], lensplit*n,
                        endpoint=True, retstep=True)
    # interpolating reduces the variance and possibly changes the avg
    y = np.interp(x,xp,yp)
    
    data = np.zeros((lensplit*n,2))
    data[:,0] = x + newstep
    # make sure that the average stays the same:
    data[:,1] = y - np.average(y) + np.average(yp)
    
    return np.split(data,n)
    
