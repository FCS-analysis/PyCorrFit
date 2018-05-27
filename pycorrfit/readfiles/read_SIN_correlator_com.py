"""correlator.com .sin files"""
import csv
import os

import numpy as np


class OpenSINError(BaseException):
    pass


def openSIN(dirname, filename):
    """Parse .sin files (correlator.com)"""
    path = os.path.join(dirname, filename)
    with open(path) as fd:
        data = fd.readlines()
    
    for line in data:
        line = line.strip()
        if line.lower().startswith("mode"):
            mode = line.split("=")[1].strip().split()
            # Find out what kind of mode it is
            
            # The rationale is that when the mode
            # consists of single characters separated
            # by empty spaces, then we have integer mode.
            if len(mode) - np.sum([len(m) for m in mode]) == 0:
                return openSIN_integer_mode(path)
            else:
                return openSIN_old(path)


def openSIN_integer_mode(path):
    """Integer mode file format of e.g. flex03lq-1 correlator (correlator.com)
    
    This is a file format where the type (AC/CC) of the curve is
    determined using integers in the "Mode=" line, e.g.
    
         Mode= 2    3    3    2    0    1    1    0
    
    which means the first correlation is CC23, the second CC32,
    the third CC01, and the fourth CC10. Similarly, 
    
        Mode= 1    1    2    2    0    4    4    4
    
    would translate to AC11, AC22, CC04, and AC44.
    """
    with open(path) as fd:
        data = fd.readlines()

    # get mode (curve indices)
    for line in data:
        line = line.strip()
        if line.lower().startswith("mode"):
            mode = line.split("=")[1].strip().split()
            mode = [ int(m) for m in mode ]
            if len(mode) % 2 != 0:
                msg = "mode must be multiples of two: {}".format(path)
                raise OpenSINError(msg)
    
    # build up the lists
    corr_func = []
    intensity = []
    section = ""
    
    # loop through lines
    for line in data:
        line = line.strip().lower()
        if line.startswith("["):
            section = line
            continue
        elif (len(line) == 0 or
              line.count("=")):
            continue

        if section.count("[correlationfunction]"):
            corr_func.append(line.split())
        elif section.count("[intensityhistory]"):
            intensity.append(line.split())

    # corr_func now contains lag time, and correlations according
    # to the mode parameters.
    corr_func = np.array(corr_func, dtype=float)
    intensity = np.array(intensity, dtype=float)

    timefactor = 1000 # because we want ms instead of s
    timedivfac = 1000 # because we want kHz instead of Hz
    intensity[:,0] *= timefactor
    corr_func[:,0] *= timefactor
    intensity[:,1:] /= timedivfac
    
    # correlator.com correlation is normalized to 1, not to 0
    corr_func[:,1:] -= 1

    # Now sort the information for pycorrfit
    correlations = []
    traces = []
    curvelist = []
    
    for ii in range(len(mode)//2):
        modea = mode[2*ii]
        modeb = mode[2*ii+1]
        
        if modea == modeb:
            # curve type AC
            curvelist.append("AC{}".format(modea))
            # trace
            atrace = np.zeros((intensity.shape[0],2), dtype=float)
            atrace[:,0] = intensity[:, 0]
            atrace[:,1] = intensity[:, modea+1]
            traces.append(atrace)
        else:
            # curve type CC
            curvelist.append("CC{}{}".format(modea,modeb))
            # trace
            modmin = min(modea, modeb)
            modmax = max(modea, modeb)
            tracea = np.zeros((intensity.shape[0],2), dtype=float)
            tracea[:,0] = intensity[:, 0]
            tracea[:,1] = intensity[:, modmin+1]
            traceb = np.zeros((intensity.shape[0],2), dtype=float)
            traceb[:,0] = intensity[:, 0]
            traceb[:,1] = intensity[:, modmax+1]            
            traces.append([tracea, traceb])
        # correlation
        corr = np.zeros((corr_func.shape[0],2), dtype=float)
        corr[:,0] = corr_func[:, 0]
        corr[:,1] = corr_func[:, ii+1]
        correlations.append(corr)

    dictionary = {}
    dictionary["Correlation"] = correlations
    dictionary["Trace"] = traces
    dictionary["Type"] = curvelist
    filelist = []
    for _i in curvelist:
        filelist.append(os.path.basename(path))
    dictionary["Filename"] = filelist
    return dictionary


def openSIN_old(path):
    """Parses the simple sin file format (correlator.com)
    
    Read data from a .SIN file, usually created by
    the software using correlators from correlator.com.

        FLXA
        Version= 1d

        [Parameters]
        ...
        Mode= Single Auto
        ...

        [CorrelationFunction]
        1.562500e-09	0.000000e+00
        3.125000e-09	0.000000e+00
        4.687500e-09	0.000000e+00
        ...
        1.887435e+01	1.000030e+00
        1.929378e+01	1.000141e+00
        1.971321e+01	9.999908e-01
        2.013264e+01	9.996810e-01
        2.055207e+01	1.000047e+00
        2.097150e+01	9.999675e-01
        2.139093e+01	9.999591e-01
        2.181036e+01	1.000414e+00
        2.222979e+01	1.000129e+00
        2.264922e+01	9.999285e-01
        2.306865e+01	1.000077e+00
        ...
        3.959419e+02	0.000000e+00
        4.026528e+02	0.000000e+00
        4.093637e+02	0.000000e+00
        4.160746e+02	0.000000e+00
        4.227854e+02	0.000000e+00
        4.294963e+02	0.000000e+00

        [RawCorrelationFunction]
        ...

        [IntensityHistory]
        TraceNumber= 458
        0.000000	9.628296e+03	9.670258e+03
        0.262144	1.001358e+04	9.971619e+03
        0.524288	9.540558e+03	9.548188e+03
        0.786432	9.048462e+03	9.010315e+03
        1.048576	8.815766e+03	8.819580e+03
        1.310720	8.827210e+03	8.861542e+03
        1.572864	9.201050e+03	9.185791e+03
        1.835008	9.124756e+03	9.124756e+03
        2.097152	9.059906e+03	9.029389e+03
        ...

    1. We are interested in the "[CorrelationFunction]" section,
    where the first column denotes tau in seconds and the second row the
    correlation signal. Values are separated by a tabulator "\t".
    We do not import anything from the "[Parameters]" section.
    We have to subtract "1" from the correlation function, since it
    is a correlation function that converges to "1" and not to "0".

    2. We are also interested in the "[IntensityHistory]" section.
    If we are only interested in autocorrelation functions: An email
    from Jixiang Zhu - Correlator.com (2012-01-22) said, that
    "For autocorrelation mode, the 2nd and 3 column represent the same
    intensity series with slight delay.  Therefore, they are statistically
    the same but numerically different."
    It is therefore perfectly fine to just use the 2nd column.

    Different acquisition modes:
    Mode            [CorrelationFunction]               [IntensityHistory]
    Single Auto     2 Colums (tau,AC)                   1 significant
    Single Cross    2 Colums (tau,CC)                   2
    Dual Auto       3 Colums (tau,AC1,AC2)              2
    Dual Cross      3 Colums (tau,CC12,CC21)            2
    Quad            5 Colums (tau,AC1,AC2,CC12,CC21)    2

    Returns:
    [0]:
     N arrays with tuples containing two elements:
     1st: tau in ms
     2nd: corresponding correlation signal
    [1]:
     N Intensity traces:
     1st: time in ms
     2nd: Trace in kHz
    [2]: 
     A list with N elements, indicating, how many correlation
     curves we are importing.
    """
    with open(path) as fd:
        Alldata = fd.readlines()
    # Find out where the correlation function and trace are
    for i in np.arange(len(Alldata)):
        if Alldata[i][0:4] == "Mode":
         
            Mode = Alldata[i].split("=")[1].strip()
        if Alldata[i][0:21] == "[CorrelationFunction]":
            StartC = i+1
        if Alldata[i][0:24] == "[RawCorrelationFunction]":
            EndC = i-2
        if Alldata[i][0:18] == "[IntensityHistory]":
            # plus 2, because theres a line with the trace length
            StartT = i+2 
        if Alldata[i][0:11] == "[Histogram]":
            EndT = i-2
    curvelist = []
    correlations = []
    traces = []
    # Get the correlation function
    Truedata = Alldata[StartC:EndC]
    timefactor = 1000 # because we want ms instead of s
    readcorr = csv.reader(Truedata, delimiter='\t')
    # Trace
    # Trace is stored in three columns
    # 1st column: time [s]
    # 2nd column: trace [Hz] 
    # 3rd column: trace [Hz] - Single Auto: equivalent to 2nd
    # Get the trace
    Tracedata = Alldata[StartT:EndT]
    # timefactor = 1000 # because we want ms instead of s
    timedivfac = 1000 # because we want kHz instead of Hz
    readtrace = csv.reader(Tracedata, delimiter='\t')
    # Process all Data:
    if Mode == "Single Auto":
        curvelist.append("AC")
        corrdata = []
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata.append((np.float(row[0])*timefactor, np.float(row[1])-1))
        correlations.append(np.array(corrdata))
        trace = []
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace.append((np.float(row[0])*timefactor,
                         np.float(row[1])/timedivfac))
        traces.append(np.array(trace))
    elif Mode == "Single Cross":
        curvelist.append("CC")
        corrdata = []
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata.append((np.float(row[0])*timefactor, np.float(row[1])-1))
        correlations.append(np.array(corrdata))
        trace1 = []
        trace2 = []
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace1.append((np.float(row[0])*timefactor,
                           np.float(row[1])/timedivfac))
            trace2.append((np.float(row[0])*timefactor,
                           np.float(row[2])/timedivfac))
        traces.append([np.array(trace1), np.array(trace2)])
    elif Mode == "Dual Auto":
        curvelist.append("AC1")
        curvelist.append("AC2")
        corrdata1 = []
        corrdata2 = []
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata1.append((np.float(row[0])*timefactor, np.float(row[1])-1))
            corrdata2.append((np.float(row[0])*timefactor, np.float(row[2])-1))
        correlations.append(np.array(corrdata1))
        correlations.append(np.array(corrdata2))
        trace1 = []
        trace2 = []
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace1.append((np.float(row[0])*timefactor,
                           np.float(row[1])/timedivfac))
            trace2.append((np.float(row[0])*timefactor,
                           np.float(row[2])/timedivfac))
        traces.append(np.array(trace1))
        traces.append(np.array(trace2))
    elif Mode == "Dual Cross":
        curvelist.append("CC12")
        curvelist.append("CC21")
        corrdata1 = []
        corrdata2 = []
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata1.append((np.float(row[0])*timefactor, np.float(row[1])-1))
            corrdata2.append((np.float(row[0])*timefactor, np.float(row[2])-1))
        correlations.append(np.array(corrdata1))
        correlations.append(np.array(corrdata2))
        trace1 = []
        trace2 = []
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace1.append((np.float(row[0])*timefactor,
                           np.float(row[1])/timedivfac))
            trace2.append((np.float(row[0])*timefactor,
                           np.float(row[2])/timedivfac))
        traces.append([np.array(trace1), np.array(trace2)])
        traces.append([np.array(trace1), np.array(trace2)])
    elif Mode == "Quad":
        curvelist.append("AC1")
        curvelist.append("AC2")
        curvelist.append("CC12")
        curvelist.append("CC21")
        corrdata1 = []
        corrdata2 = []
        corrdata12 = []
        corrdata21 = []
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata1.append((np.float(row[0])*timefactor, np.float(row[1])-1))
            corrdata2.append((np.float(row[0])*timefactor, np.float(row[2])-1))
            corrdata12.append((np.float(row[0])*timefactor, np.float(row[3])-1))
            corrdata21.append((np.float(row[0])*timefactor, np.float(row[4])-1))
        correlations.append(np.array(corrdata1))
        correlations.append(np.array(corrdata2))
        correlations.append(np.array(corrdata12))
        correlations.append(np.array(corrdata21))
        trace1 = []
        trace2 = []
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace1.append((np.float(row[0])*timefactor,
                           np.float(row[1])/timedivfac))
            trace2.append((np.float(row[0])*timefactor,
                           np.float(row[2])/timedivfac))
        traces.append(np.array(trace1))
        traces.append(np.array(trace2))
        traces.append([np.array(trace1), np.array(trace2)])
        traces.append([np.array(trace1), np.array(trace2)])
    else:
        raise NotImplemented(
                    "'Mode' type '{}' in {} not supported by this method!".
                    Mode, format(path))
        
    dictionary = {}
    dictionary["Correlation"] = correlations
    dictionary["Trace"] = traces
    dictionary["Type"] = curvelist
    filelist = []
    for i in curvelist:
        filelist.append(os.path.basename(path))
    dictionary["Filename"] = filelist

    return dictionary
