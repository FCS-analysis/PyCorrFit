"""PyCorrFit loader"""
from os.path import dirname, abspath, split
import sys

sys.path = [split(abspath(dirname(__file__)))[0]] + sys.path
from pycorrfit.gui import main  # noqa: E402


if __name__ == "__main__":
    main.Main()
