# -*- coding: utf-8 -*-
"""
methods to open ALV .ASC files
"""
from __future__ import division

import os
import csv
import numpy as np


def openASC(dirname, filename):
    """ 
    Read data from a ALV .ASC files.
    """
    path = os.path.join(dirname, filename)
    with open(path, 'r') as openfile:
        Alldata = openfile.readlines()
    
    # Open special format?
    filetype = Alldata[0].strip() 
    if filetype in ["ALV-7004/USB"]:
        return openASC_ALV_7004_USB(path)
    else:
        # last resort
        return openASC_old(path)


def openASC_old(path):
    """ Read data from a .ASC file, created by
        some ALV-6000 correlator.

            ALV-6000/E-WIN Data
            Date :    "2/20/2012"
            ...
            "Correlation"
              1.25000E-004      3.00195E-001
              2.50000E-004      1.13065E-001
              3.75000E-004      7.60367E-002
              5.00000E-004      6.29926E-002
              6.25000E-004      5.34678E-002
              7.50000E-004      4.11506E-002
              8.75000E-004      4.36752E-002
              1.00000E-003      4.63146E-002
              1.12500E-003      3.78226E-002
            ...
              3.35544E+004     -2.05799E-006
              3.77487E+004      4.09032E-006
              4.19430E+004      4.26295E-006
              4.61373E+004      1.40265E-005
              5.03316E+004      1.61766E-005
              5.45259E+004      2.19541E-005
              5.87202E+004      3.26527E-005
              6.29145E+004      2.72920E-005

            "Count Rate"
               1.17188          26.77194
               2.34375          26.85045
               3.51563          27.06382
               4.68750          26.97932
               5.85938          26.73694
               7.03125          27.11332
               8.20313          26.81376
               9.37500          26.82741
              10.54688          26.88801
              11.71875          27.09710
              12.89063          27.13209
              14.06250          27.02200
              15.23438          26.95287
              16.40625          26.75657
              17.57813          26.43056
            ...
             294.14063          27.22597
             295.31250          26.40581
             296.48438          26.33497
             297.65625          25.96457
             298.82813          26.71902

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
    filename = os.path.basename(path)
    with open(path, 'r') as openfile:
        Alldata = openfile.readlines()
    # End of trace
    EndT = Alldata.__len__()
    ## Correlation function
    # Find out where the correlation function is
    for i in np.arange(len(Alldata)):
        if Alldata[i].startswith('Mode'):
            mode = Alldata[i][5:].strip(' ":').strip().strip('"')
            single_strings = ["a-ch0", "a-ch1", "auto ch0", "auto ch1",
                              "fast auto ch0", "fast auto ch1",
                               ]
            if (mode.lower().count('single') or
                mode.lower().strip() in single_strings):
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
            # takes care of "Count Rate" and "Countrate"
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
    # Add lists to *data* according to the length of *curvelist*
    data = [[]]*len(curvelist)
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


def openASC_ALV_7004_USB(path):
    """
    Opens ALV file format with header information "ALV-7004/USB" 
    
    This is a single-run file format.
    - data is identified by 4*"\t"
    - count rate is identified by string (also "countrate")
    - allzero-correlations are removed

    "Correlation"
      2.50000E-005     -9.45478E-001     -1.00000E+000      5.22761E-002      3.05477E-002
      5.00000E-005      6.73734E-001     -2.59938E-001      3.17894E-002      4.24466E-002
      7.50000E-005      5.30716E-001      3.21605E-001      5.91051E-002      2.93061E-002
      1.00000E-004      3.33292E-001      1.97860E-001      3.24102E-002      3.32379E-002
      1.25000E-004      2.42538E-001      1.19988E-001      4.37917E-002      3.05477E-002
      1.50000E-004      1.86396E-001      1.23318E-001      5.66218E-002      2.25806E-002
      1.75000E-004      1.73836E-001      8.53991E-002      4.64819E-002      3.46865E-002
      2.00000E-004      1.48080E-001      9.35377E-002      4.37917E-002      4.17223E-002
    [...]
      1.00663E+004      2.80967E-005     -2.23975E-005     -7.08272E-005      5.70470E-005
      1.09052E+004      9.40185E-005      2.76261E-004      1.29745E-004      2.39958E-004
      1.17441E+004     -2.82103E-004     -1.97386E-004     -2.88753E-004     -2.60987E-004
      1.25829E+004      1.42069E-004      3.82018E-004      6.03932E-005      5.40363E-004
    
    "Count Rate"
           0.11719         141.83165          81.54211         141.83165          81.54211
           0.23438         133.70215          77.90344         133.70215          77.90344
           0.35156         129.67148          74.58858         129.67148          74.58858
           0.46875         134.57133          79.53957         134.57133          79.53957
    [...]
          29.29688         143.78307          79.06236         143.78307          79.06236
          29.41406         154.80135          82.87147         154.80135          82.87147
          29.53125         187.43013          89.61197         187.43013          89.61197
          29.64844         137.82655          77.71597         137.82655          77.71597
    [...]


    """
    filename = os.path.basename(path)
    with open(path, 'r') as openfile:
        Alldata = openfile.readlines()
    
    # Find the different arrays
    # correlation array: "  "
    # trace array: "       "
    Allcorr = list()
    Alltrac = list()
    i=0
    intrace = False
    for item in Alldata:
        if item.lower().strip().strip('"').replace(" ", "") == "countrate":
            intrace = True
        i += 1
        if item.count("\t") == 4: 
            if intrace:
                it = item.split("\t")
                it = [ float(t.strip()) for t in it ]
                Alltrac.append(it)
            else:
                ic = item.split("\t")
                ic = [ float(c.strip()) for c in ic ]
                Allcorr.append(ic)
    Allcorr = np.array(Allcorr)
    Alltrac = np.array(Alltrac)
    
    # Allcorr: lag time, ac1, ac2, cc12, cc21
    # Alltrac: time, trace1, trace2, trace1, trace2
    assert np.allclose(Alltrac[:,1], Alltrac[:,3], rtol=.01), "unknown ALV file format"
    assert np.allclose(Alltrac[:,2], Alltrac[:,4], rtol=.01), "unknown ALV file format"
    
    guesstypelist = ["AC1", "AC2", "CC12", "CC21"]
    typelist = list()
    corrlist = list()
    tracelist = list()
    filelist = list()
    
    lagtime = Allcorr[:,0]
    time = Alltrac[:,0]*1000
    trace1 = np.dstack((time, Alltrac[:,1]))[0]
    trace2 = np.dstack((time, Alltrac[:,2]))[0]
    
    for i, typ in enumerate(guesstypelist):
        corr = np.dstack((lagtime, Allcorr[:,i+1]))[0]
        
        if not np.allclose(corr[:,1], np.zeros_like(lagtime)):
            # type
            typelist.append(typ)
            # correlation
            corrlist.append(corr)
            # trace
            if typ.count("CC"):
                tracelist.append([trace1, trace2])
            elif typ.count("AC1"):
                tracelist.append([trace1])
            elif typ.count("AC2"):
                tracelist.append([trace2])
            else:
                raise ValueError("Unknown ALV file format")
            # filename
            filelist.append(filename)

    dictionary = dict()
    dictionary["Correlation"] = corrlist
    dictionary["Trace"] = tracelist
    dictionary["Type"] = typelist
    dictionary["Filename"] = filelist
    return dictionary


def mysplit(a, n):
    """
       Split a trace into n equal parts by interpolation.
       The signal average is preserved, but the signal variance will
       decrease.
    """
    if n <= 1:
        return [np.array(a)]
    a = np.array(a)
    N = len(a)
    lensplit = np.int(np.ceil(N/n))

    # xp is actually rounded -> recalculate
    xp = np.linspace(a[:,0][0], a[:,0][-1], N,  endpoint=True)
    
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
    
