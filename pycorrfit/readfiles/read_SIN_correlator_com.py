# -*- coding: utf-8 -*-
"""
method to open correlator.com .sin files
"""
import os
import csv
import numpy as np


def openSIN(dirname, filename):
    """ Read data from a .SIN file, usually created by
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
    openfile = open(os.path.join(dirname, filename), 'r')
    Alldata = openfile.readlines()
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
    curvelist = list()
    correlations = list()
    traces = list()
    # Get the correlation function
    Truedata = Alldata.__getslice__(StartC, EndC)
    timefactor = 1000 # because we want ms instead of s
    readcorr = csv.reader(Truedata, delimiter='\t')
    # Trace
    # Trace is stored in three columns
    # 1st column: time [s]
    # 2nd column: trace [Hz] 
    # 3rd column: trace [Hz] - Single Auto: equivalent to 2nd
    # Get the trace
    Tracedata = Alldata.__getslice__(StartT, EndT)
    # timefactor = 1000 # because we want ms instead of s
    timedivfac = 1000 # because we want kHz instead of Hz
    readtrace = csv.reader(Tracedata, delimiter='\t')
    openfile.close()
    # Process all Data:
    if Mode == "Single Auto":
        curvelist.append("AC")
        corrdata = list()
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata.append((np.float(row[0])*timefactor, np.float(row[1])-1))
        correlations.append(np.array(corrdata))
        trace = list()
        for row in readtrace:
            # tau in ms, corr-function minus "1"
            trace.append((np.float(row[0])*timefactor,
                         np.float(row[1])/timedivfac))
        traces.append(np.array(trace))
    elif Mode == "Single Cross":
        curvelist.append("CC")
        corrdata = list()
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata.append((np.float(row[0])*timefactor, np.float(row[1])-1))
        correlations.append(np.array(corrdata))
        trace1 = list()
        trace2 = list()
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
        corrdata1 = list()
        corrdata2 = list()
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata1.append((np.float(row[0])*timefactor, np.float(row[1])-1))
            corrdata2.append((np.float(row[0])*timefactor, np.float(row[2])-1))
        correlations.append(np.array(corrdata1))
        correlations.append(np.array(corrdata2))
        trace1 = list()
        trace2 = list()
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
        corrdata1 = list()
        corrdata2 = list()
        for row in readcorr:
            # tau in ms, corr-function minus "1"
            corrdata1.append((np.float(row[0])*timefactor, np.float(row[1])-1))
            corrdata2.append((np.float(row[0])*timefactor, np.float(row[2])-1))
        correlations.append(np.array(corrdata1))
        correlations.append(np.array(corrdata2))
        trace1 = list()
        trace2 = list()
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
        corrdata1 = list()
        corrdata2 = list()
        corrdata12 = list()
        corrdata21 = list()
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
        trace1 = list()
        trace2 = list()
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
    dictionary = dict()
    dictionary["Correlation"] = correlations
    dictionary["Trace"] = traces
    dictionary["Type"] = curvelist
    filelist = list()
    for i in curvelist:
        filelist.append(filename)
    dictionary["Filename"] = filelist
    return dictionary
