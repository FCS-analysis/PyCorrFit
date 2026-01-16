from os.path import dirname, exists, join, realpath
from urllib.request import urlretrieve

from setuptools import setup

# Download documentation if it was not compiled with latex
pdfdoc = join(dirname(realpath(__file__)), "doc/PyCorrFit_doc.pdf")
webdoc = "https://github.com/FCS-analysis/PyCorrFit/wiki/PyCorrFit_doc.pdf"
if not exists(pdfdoc):
    print("Downloading {} from {}".format(pdfdoc, webdoc))
    try:
        urlretrieve(webdoc, pdfdoc)
    except Exception as _e:
        print("Failed to download documentation.")

setup()
