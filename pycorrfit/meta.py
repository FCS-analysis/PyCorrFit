# -*- coding: utf-8 -*-
"""
meta data and methods for PyCorrFit
"""

import os
import sys


def find_program(program):
    """ Uses the systems PATH variable find executables"""
    path = os.environ['PATH']
    paths = path.split(os.pathsep)
    for d in paths:
        if os.path.isdir(d):
            fullpath = os.path.join(d, program)
            if sys.platform[:3] == 'win':
                for ext in '.exe', '.bat':
                    program_path = fullpath + ext
                    if os.path.isfile(fullpath + ext):
                        return (1, program_path)
            else:
                if os.path.isfile(fullpath):
                    return (1, fullpath)
    return (0, None)


def get_file_location(filename):
    """
    Locate non-Python files that are part of PyCorrFit.
    """
    dirname = os.path.dirname(os.path.abspath(__file__))
    locations = ["/./", "/pycorrfit_doc/", "/doc/"]
    locations += [ "/.."+l for l in locations]
    locations = [ os.path.realpath(dirname+l) for l in locations]

    for i in range(len(locations)):
        # check /usr/lib64/32 -> /usr/lib
        for larch in ["lib32", "lib64"]:
            if dirname.count(larch):
                locations.append(locations[i].replace(larch, "lib", 1))
    
    ## freezed binaries:
    if hasattr(sys, 'frozen'):
        try:
            adir = sys._MEIPASS + "/doc/"  # @UndefinedVariable
        except:
            adir = "./"
        locations.append(os.path.realpath(adir))
    for loc in locations:
        thechl = os.path.join(loc,filename)
        if os.path.exists(thechl):
            return thechl
            break
    # if this does not work:
    return None


def get_version():
    """
    Get the version.
    """
    StaticChangeLog = get_file_location("ChangeLog.txt")

    # Check if we can extract the version
    try:
        clfile = open(StaticChangeLog, 'r')
        version = clfile.readline().strip()
        clfile.close()     
    except:
        version = "0.0.0-unknown"
        
        
    return version