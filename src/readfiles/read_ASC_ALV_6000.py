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
    ## Correlation function
    # Find out where the correlation function is
    for i in np.arange(len(Alldata)):
        if Alldata[i][0:13] == '"Correlation"':
            # Start of correlation function
            StartC = i+1
        if Alldata[i][0:31] == '"Correlation (Multi, Averaged)"':
            # Start of AVERAGED correlation function !!!
            # There are several curves now.
            StartC = i+2
        if Alldata[i][0:12] == '"Count Rate"':
            # End of correlation function
            EndC = i-2
            # Start of trace (goes until end of file)
            StartT = i+1
    EndT = Alldata.__len__()
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
    # Add lists to *trace* according to the length of *curvelist*
    for item in curvelist:
        trace.append(list())
    # Work through the rows
    for row in readtrace:
        # tau in ms, corr-function
        trace[0].append((np.float(row[0])*timefactor, np.float(row[1])))
        for i in np.arange(len(curvelist)-1):
            trace[i+1].append((np.float(row[0])*timefactor, 0))
    # return as an array
    openfile.close()
    dictionary = dict()
    dictionary["Correlation"] = np.array(data)
    dictionary["Trace"] = np.array(trace)
    dictionary["Type"] = curvelist
    filelist = list()
    for i in curvelist:
        filelist.append(filename)
    dictionary["Filename"] = filelist
    return dictionary
