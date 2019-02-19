"""Main execution script"""
from distutils.version import LooseVersion
import sys
import warnings

import yaml
import numpy as np
import scipy


class Fake(object):
    """ Fake module.
    """

    def __init__(self):
        self.__version__ = "0.0 unknown"
        self.version = "0.0 unknown"
        self.use = lambda x: None


# Import matplotlib a little earlier. This way some problems with saving
# dialogs that are not made by "WXAgg" are solved.
try:
    import matplotlib
except ImportError:
    matplotlib = Fake()
# We do catch warnings about performing this before matplotlib.backends stuff
# matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    matplotlib.use('WXAgg')  # Tells matplotlib to use WxWidgets for dialogs


# Sympy is optional:
try:
    import sympy
except ImportError:
    print("Importing sympy failed! Checking of external model functions")
    print("will not work!")
    # We create a fake module sympy with a __version__ property.
    # This way users can run PyCorrFit without having installed sympy.
    sympy = Fake()

# We must not import wx here. frontend/gui does that. If we do import wx here,
# somehow unicode characters will not be displayed correctly on windows.
# import wx

# Continue with the import:
from . import frontend as gui  # noqa: E402
from . import doc  # noqa: E402


def CheckVersion(given, required, name):
    """ For a given set of versions  str *required* and str *given*,
    where version are usually separated by dots, print whether for
    the module str *name* the required verion is met or not.
    """
    try:
        req = LooseVersion(required)
        giv = LooseVersion(given)
    except:
        print(" WARNING: Could not verify version of "+name+".")
        return
    if req > giv:
        print(" WARNING: You are using "+name+" v. "+given +
              " | Required: "+name+" " + required)
    else:
        print(" OK: "+name+" v. "+given+" | "+required+" required")


# Start gui
def Main():

    # VERSION
    version = doc.__version__
    __version__ = version

    print(gui.doc.info(version))

    # Check important module versions
    print("\n\nChecking module versions...")
    CheckVersion(matplotlib.__version__, "2.2.2", "matplotlib")
    CheckVersion(np.__version__, "1.14.2", "NumPy")
    CheckVersion(yaml.__version__, "3.12", "PyYAML")
    CheckVersion(scipy.__version__, "1.0.1", "SciPy")
    CheckVersion(sympy.__version__, "1.1.1", "sympy")
    CheckVersion(gui.wx.__version__, "4.0.1", "wxPython")

    # Start gui
    app = gui.MyApp(False)

    frame = gui.MyFrame(None, -1, version)
    app.frame = frame

    # Before starting the main loop, check for possible session files
    # in the arguments.
    sysarg = sys.argv
    for arg in sysarg:
        if arg.endswith(".pcfs"):
            print("\nLoading Session "+arg)
            frame.OnOpenSession(sessionfile=arg)
            break
        if arg.endswith(".fcsfit-session.zip"):
            print("\nLoading Session "+arg)
            frame.OnOpenSession(sessionfile=arg)
            break
        elif arg[:6] == "python":
            pass
        elif arg[-12:] == "PyCorrFit.py":
            pass
        elif arg[-11:] == "__main__.py":
            pass
        else:
            print("Ignoring command line parameter: "+arg)

    app.MainLoop()


if __name__ == "__main__":
    Main()
