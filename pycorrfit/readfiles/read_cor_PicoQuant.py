"""PicoQuant .cor files"""
import csv
import pathlib
import warnings

import numpy as np

class LoadCORError(BaseException):
    pass

def get_header_index(L, elem):
    try:
        index = L.index(elem)
    except ValueError:
        raise ValueError(f'Expected {elem} in the data header, but found only {L}')

    return index

def openCOR(path, filename=None):
    """
    Read data from a PicoQuant .cor file.

    This format consists of a metadata header, a blank line, then a
    whitespace-delimited data header followed by a data array.
    ------------------------------------------------------------
    TTTR Correlator Export
    PicoHarp Software version 3.0.0.3 format version 3.0
    Raw data: c:\\users\\baker lab 432-a\\desktop\\grant fcs\\default_013.ptu
    Recorded: 16/12/22 17:40:13
    Mode: T2
    Routing Mask A: 0 1 0 0 0
    Routing Mask B: 1 0 0 0 0
    Start time [s]: 0.000000
    Time span [s]: 7.545534
    Counts A: 382989
    Counts B: 523316
    Tau resolution [s]: 0.00000002500000

     taustep       tau/s        G(A,A)    G(B,B)    G(A,B)
          6     0.0000001500    0.8375    0.3556    0.1708
          7     0.0000001750    0.6503    0.2652    0.1445
          9     0.0000002250    0.5680    0.2173    0.1264
         11     0.0000002750    0.4836    0.1594    0.1614
         13     0.0000003250    0.3241    0.1528    0.1486
         15     0.0000003750    0.2819    0.1236    0.1641
         17     0.0000004250    0.3591    0.1467    0.1102
    [...]
    ------------------------------------------------------------

    Returns:
    A dictionary containing:
       Trace: list of 2d np.array containing two columns:
              1st: tau in ms
              2nd: corresponding correlation signal
       Type: list of strings indictating the type of each correlation
       Filename: the basename for each file loaded
       Trace: blank list, since cor does not store intensity traces
    """
    path = pathlib.Path(path)
    if filename is not None:
        warnings.warn("Using `filename` is deprecated.", DeprecationWarning)
        path = path / filename
    filename = path.name
    
    s_to_ms = 1000 # cor provides seconds, we want ms

    corfile = path.open('r', encoding='utf-8')
    header = list()
    for line in corfile:
        header.append(line.strip())
        if header[-1] == '':
            break

    if header[0] != 'TTTR Correlator Export':
        raise ValueError(f'Error while reading {path.name}. Expected the first line to be "TTTR Correlator Export"')        

    data_header = next(corfile).split()
    data = np.loadtxt(corfile)
    
    tau = data[:, get_header_index(data_header, 'tau/s')]*s_to_ms
    correlation_names = ['G(A,A)', 'G(A,B)', 'G(B,B)']
    correlation_types = ['AC',     'CC',     'AC'    ]
    correlations = list()

    for correlation_name in correlation_names:
        correlation = data[:, get_header_index(data_header, correlation_name)]
        cor = np.zeros((len(correlation), 2), dtype=correlation.dtype)
        cor[:, 0] = tau
        cor[:, 1] = correlation
        correlations.append(cor)
        
    dictionary = dict()
    dictionary['Correlation'] = correlations
    dictionary['Trace'] = [[] for _ in dictionary['Correlation']]
    dictionary['Type'] = correlation_types
    dictionary['Filename'] = [path.name for _ in dictionary['Correlation']]
    return dictionary
