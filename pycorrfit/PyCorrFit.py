from pycorrfit.gui import main
"""PyCorrFit loader"""
from os.path import dirname, abspath, split
import sys

sys.path = [split(abspath(dirname(__file__)))[0]] + sys.path


if __name__ == "__main__":
    main.Main()
