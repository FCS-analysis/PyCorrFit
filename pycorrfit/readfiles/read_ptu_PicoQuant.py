"""Read PicoQuant PTU files (t2 and t3 mode)"""


from .read_pt3_PicoQuant import openPT3


def openPTU(path, filename=None):
    return openPT3(path, filename)
