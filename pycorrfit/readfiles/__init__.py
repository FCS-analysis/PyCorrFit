"""Module readfiles: Import correlation data from data files"""
import csv
import io
import pathlib
import shutil
import sys
import tempfile
import warnings
import zipfile

import numpy as np
import yaml

# To add a filetype add it here and in the
# dictionaries at the end of this file.
from .read_ASC_ALV import openASC
from .read_CSV_PyCorrFit import openCSV
from .read_SIN_correlator_com import openSIN
from .read_FCS_Confocor3 import openFCS
from .read_mat_ries import openMAT
from .read_pt3_PicoQuant import openPT3


def add_all_supported_filetype_entry(adict):
    wildcard = ""
    keys = adict.keys()
    N = len(keys)
    i = 0
    for key in keys:
        newwc = key.split("|")[1]
        wildcard = wildcard + newwc
        i = i + 1
        if i != N:
            wildcard = wildcard + ";"
    adict[ALL_SUP_STRING+"|"+wildcard] = open_any


def get_supported_extensions():
    """
    Returns list of extensions of currently supported file types.
    """
    extlist = []
    for kf in list(filetypes_dict.keys()):
        ext = kf.split("|")[-1]
        ext = ext.split(";")
        ext = [e.lower().strip("*. ") for e in ext]
        ext = list(np.unique(ext))
        extlist += ext
    extlist = list(np.unique(extlist))
    extlist.sort()
    return extlist


# To increase user comfort, we will now create a file opener thingy that
# knows how to open all files we know.
def open_any(path, filename=None):
    """Open a supported data file

    Parameters
    ----------
    path : str
        Full path to file or directory containing `filename`
    filename : str
        The name of the file if not given in path (optional).
    """
    path = pathlib.Path(path)
    if filename is not None:
        warnings.warn("Using `filename` is deprecated.", DeprecationWarning)
        path = path / filename
    wildcard = path.suffix
    for key in filetypes_dict.keys():
        # Recurse into the wildcards
        wildcardstring = key.split("|")
        # We do not want to recurse
        if wildcardstring[0] != ALL_SUP_STRING:
            otherwcs = wildcardstring[1].split(";")
            for wc in otherwcs:
                if wc.strip("*") == wildcard:
                    return filetypes_dict[key](path)
    else:
        # If we could not find the correct function in filetypes_dict,
        # try again in filetypes_bg_dict:
        return open_any_bg(path)


def open_any_bg(path, filename=None):
    path = pathlib.Path(path)
    if filename is not None:
        warnings.warn("Using `filename` is deprecated.", DeprecationWarning)
        path = path / filename

    wildcard = path.suffix
    for key in filetypes_bg_dict.keys():
        # Recurse into the wildcards
        wildcardstring = key.split("|")
        # We do not want to recurse
        if wildcardstring[0] != ALL_SUP_STRING:
            otherwcs = wildcardstring[1].split(";")
            for wc in otherwcs:
                if wc.strip("*") == wildcard:
                    return filetypes_bg_dict[key](path)
    else:
        # For convenience in openZIP
        return None


def openZIP(path, filename=None):
    """Load everything inside a .zip file that could be an FCS curve.

    Will use any wildcard in `filetypes_dict`.
    """
    #    It's a rather lengthy import of the session file. The code is copied
    #    from openfile.OpenSession. The usual zip file packed curves are
    #    imported on the few code lines after the else statement.

    path = pathlib.Path(path)
    if filename is not None:
        warnings.warn("Using `filename` is deprecated.", DeprecationWarning)
        path = path / filename
    filename = path.name

    # Open the archive:
    Arc = zipfile.ZipFile(path, mode='r')
    Correlations = []  # Correlation information
    Curvelist = []    # Type information
    Filelist = []     # List of filenames corresponding to *Curvelist*
    Trace = []        # Corresponding traces
    # First test, if we are opening a session file
    sessionwc = [".fcsfit-session.zip", ".pcfs"]
    if filename.endswith(sessionwc[0]) or filename.endswith(sessionwc[1]):
        # Get the yaml parms dump:
        yamlfile = Arc.open("Parameters.yaml")
        # Parms: Fitting and drawing parameters of the correlation curve
        # The *yamlfile* is responsible for the order of the Pages #i.
        # The parameters are actually useless to us right now.
        Parms = yaml.safe_load(yamlfile)
        yamlfile.close()
        # Get the correlation arrays
        ImportedNum = list()
        for i in np.arange(len(Parms)):
            # The *number* is used to identify the correct file
            number = str(Parms[i][0])
            expfilename = "data"+number[1:len(number)-2]+".csv"
            expfile = Arc.open(expfilename, 'r')
            readdata = csv.reader(io.StringIO(
                expfile.read().decode()), delimiter=',')
            dataexp = list()
            if str(readdata.__next__()[0]) == "# tau only":
                # We do not have a curve here
                pass
            else:
                Filelist.append(filename+"/#"+number[1:len(number)-2])
                for row in readdata:
                    # Exclude commentaries
                    if (str(row[0])[0:1] != '#'):
                        dataexp.append((float(row[0]), float(row[1])))
                dataexp = np.array(dataexp)
                Correlations.append(dataexp)
                ImportedNum.append(i)
            del readdata
            expfile.close()
        # Get the Traces
        for i in ImportedNum:
            # Make sure we only import those traces that had a corresponding
            # correlation curve. (ImportedNum)
            #
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
                Curvelist.append("AC")
            else:
                # Cross correlation uses two traces
                tracefilenames = ["trace"+number[1:len(number)-2]+"A.csv",
                                  "trace"+number[1:len(number)-2]+"B.csv"]
                Curvelist.append("CC")
            thistrace = list()
            for tracefilename in tracefilenames:
                try:
                    Arc.getinfo(tracefilename)
                except KeyError:
                    # No correlation curve, but add a None
                    pass
                else:
                    tracefile = Arc.open(tracefilename, 'r')
                    traceread = csv.reader(io.StringIO(
                        tracefile.read().decode()), delimiter=',')
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
            if len(thistrace) == 1:
                Trace.append(thistrace[0])
            elif len(thistrace) == 2:
                Trace.append(thistrace)
            else:
                Trace.append(None)
    else:
        # We are not importing from a session but from a zip file with
        # probably a mix of all filetypes we know. This works
        # recursively (e.g. a zip file in a zipfile).
        allfiles = Arc.namelist()
        # Extract data to temporary folder
        tempdir = pathlib.Path(tempfile.mkdtemp())
        for afile in allfiles:
            Arc.extract(afile, path=tempdir)
            data = open_any(tempdir / afile)
            if data is not None:
                Correlations += data["Correlation"]
                Trace += data["Trace"]
                Curvelist += data["Type"]
                fnames = data["Filename"]
                Filelist += [filename+"/"+fs for fs in fnames]
        shutil.rmtree(path=tempdir, ignore_errors=True)
    Arc.close()
    dictionary = {}
    dictionary["Correlation"] = Correlations
    dictionary["Trace"] = Trace
    dictionary["Type"] = Curvelist
    dictionary["Filename"] = Filelist
    return dictionary


# The string that is shown when opening all supported files
# We add an empty space so it is listed first in the dialogs.
ALL_SUP_STRING = " All supported files"

# Dictionary with filetypes that we can open
# The wildcards point to the appropriate functions.
filetypes_dict = {"Correlator.com (*.SIN)|*.SIN;*.sin": openSIN,
                  "ALV (*.ASC)|*.ASC;*.asc": openASC,
                  "PyCorrFit (*.csv)|*.csv": openCSV,
                  "Matlab 'Ries (*.mat)|*.mat": openMAT,
                  "PicoQuant (*.pt3)|*.pt3": openPT3,
                  "Zeiss ConfoCor3 (*.fcs)|*.fcs": openFCS,
                  "Zip file (*.zip)|*.zip": openZIP,
                  "PyCorrFit session (*.pcfs)|*.pcfs": openZIP
                  }
# For user comfort, add "All supported files" wildcard:
add_all_supported_filetype_entry(filetypes_dict)

# Dictionary with filetypes we can open that have intensity traces in them.
filetypes_bg_dict = {"Correlator.com (*.SIN)|*.SIN;*.sin": openSIN,
                     "ALV (*.ASC)|*.ASC": openASC,
                     "PyCorrFit (*.csv)|*.csv": openCSV,
                     "PicoQuant (*.pt3)|*.pt3": openPT3,
                     "Zeiss ConfoCor3 (*.fcs)|*.fcs": openFCS,
                     "Zip file (*.zip)|*.zip": openZIP,
                     "PyCorrFit session (*.pcfs)|*.pcfs": openZIP
                     }
add_all_supported_filetype_entry(filetypes_bg_dict)
