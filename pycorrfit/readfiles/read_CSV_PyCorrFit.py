# -*- coding: utf-8 -*-
""" 
    PyCorrFit
    
    functions in this file: *openCSV*

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


def openCSV(dirname, filename):
    """ Read relevant data from a file looking like this:
        [...]
        # Comment
        # Data type: Autocorrelation
        [...]
        1.000000e-006   3.052373e-001
        1.020961e-006   3.052288e-001
        1.042361e-006   3.052201e-001
        1.064209e-006   3.052113e-001
        1.086516e-006   3.052023e-001
        1.109290e-006   3.051931e-001
        [...]
        # BEGIN TRACE
        [...]
        10.852761   31.41818
        12.058624   31.1271
        13.264486   31.27305
        14.470348   31.33442
        15.676211   31.15861
        16.882074   31.08564
        18.087936   31.21335
        [...]

        Data type:
        If Data type is "Cross-correlation", we will try to import
        two traces after "# BEGIN SECOND TRACE"

        1st section:
         First column denotes tau in seconds and the second row the
         correlation signal.
        2nd section:
         First column denotes tau in seconds and the second row the
         intensity trace in kHz.


        Returns:
        1. A list with tuples containing two elements:
           1st: tau in ms
           2nd: corresponding correlation signal
        2. None - usually is the trace, but the trace is not saved in
                  the PyCorrFit .csv format.
        3. A list with one element, indicating, that we are opening only
           one correlation curve.
    """
    # Check if the file is correlation data
    csvfile = open(os.path.join(dirname, filename), 'r')
    firstline = csvfile.readline()
    if firstline.lower().count("this is not correlation data") > 0:
        csvfile.close()
        return None
    csvfile.close()
    
    # Define what will happen to the file
    timefactor = 1000 # because we want ms instead of s
    csvfile = open(os.path.join(dirname, filename), 'r')
    readdata = csv.reader(csvfile, delimiter=',')
    data = list()
    trace = None
    traceA = None
    DataType="AC" # May be changed
    numtraces = 0
    for row in readdata:
        if len(row) == 0 or len(str(row[0]).strip()) == 0:
            # Do nothing with empty/whitespace lines
            pass
            # Beware that the len(row) statement has to be called first
            # (before the len(str(row[0]).strip()) ). Otherwise some
            # error would be raised.
        elif str(row[0])[:12].lower() == "# Type AC/CC".lower():
            corrtype = str(row[0])[12:].strip().strip(":").strip()
            if corrtype[:17].lower() == "cross-correlation":
                # We will later try to import a second trace
                DataType="CC"
                DataType += corrtype[17:].strip()
            elif corrtype[0:15].lower() == "autocorrelation":
                DataType="AC"
                DataType += corrtype[15:].strip()         
        elif str(row[0])[0:13].upper() == '# BEGIN TRACE':
            # Correlation is over. We have a trace
            corr = np.array(data)
            data=list()
            numtraces = 1
        elif str(row[0])[0:20].upper() == '# BEGIN SECOND TRACE':
            # First trace is over. We have a second trace
            traceA = np.array(data)
            data = list()
            numtraces = 2
        # Exclude commentaries
        elif str(row[0])[0:1] != '#':
            # Read the 1st section
            # On Windows we had problems importing nan values that
            # had some white-spaces around them. Therefore: strip()
            ## As of version 0.7.8 we are supporting white space
            ## separated values as well
            if len(row) == 1:
                row = row[0].split()
            data.append((np.float(row[0].strip())*timefactor, 
                         np.float(row[1].strip())))
    # Collect the rest of the trace, if there is any:
    rest = np.array(data)
    if numtraces == 0:
        corr = rest
    elif numtraces >= 1:
        trace = rest
    del data
    ## Remove any NaN numbers from thearray
    # Explanation:
    # np.isnan(data)
    #  finds the position of NaNs in the array (True positions); 2D array, bool
    # any(1)
    #  finds the rows that have True in them; 1D array, bool
    # ~
    #  negates them and is given as an argument (array type bool) to
    #  select which items we want.
    corr = corr[~np.isnan(corr).any(1)]
    # Also check for infinities.
    corr = corr[~np.isinf(corr).any(1)]
    csvfile.close()
    Traces=list()
    # Set correct trace data for import
    if numtraces == 1 and DataType[:2] == "AC":
        Traces.append(trace)
    elif numtraces == 2 and DataType[:2] == "CC":
        Traces.append([traceA, trace])
    elif numtraces == 1 and DataType[:2] == "CC":
        # Should not happen, but for convenience:
        Traces.append([trace, trace])
    else:
        Traces.append(None)
    dictionary = dict()
    dictionary["Correlation"] = [corr]
    dictionary["Trace"] = Traces
    dictionary["Type"] = [DataType]
    dictionary["Filename"] = [filename]
    return dictionary
