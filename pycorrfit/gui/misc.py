"""Module misc: Non-science related code.
"""
import codecs

import numpy as np
import wx

# The icon file was created with
# img2py -i -n Main PyCorrFit_icon.png icon.py
from . import icon                         # Contains the program icon


def parseString2Pagenum(parent, string, nodialog=False):
    """ Parse a string with a list of pagenumbers to an integer list with
        page numbers.
        e.g. "1-3,5,7" --> [1,2,3,5,7]
        parent is important
    """
    listFull = string.split(",")
    PageNumbers = list()
    try:
        for item in listFull:
            pagerange = item.split("-")
            start = pagerange[0].strip()
            start = int("".join(filter(type(start).isdigit, start)))
            end = pagerange[-1].strip()
            end = int("".join(filter(type(end).isdigit, end)))
            for i in np.arange(end-start+1)+start:
                PageNumbers.append(i)
        PageNumbers.sort()
        return PageNumbers
    except:
        if nodialog is False:
            errstring = "Invalid syntax in page selection: "+string +\
                        ". Please use a comma separated list with" +\
                        " optional dashes, e.g. '1-3,6,8'."
            try:
                wx.MessageDialog(parent, errstring, "Error",
                                 style=wx.ICON_ERROR | wx.OK | wx.STAY_ON_TOP)
            except:
                raise ValueError(errstring)
        else:
            raise ValueError(errstring)
        return None


def parsePagenum2String(pagenumlist):
    """ Make a string with dashes and commas from a list of pagenumbers.
        e.g. [1,2,3,5,7] --> "1-3,5,7"
    """
    if len(pagenumlist) == 0:
        return ""
    # Make sure we have integers
    newlist = list()
    for num in pagenumlist:
        newlist.append(int(num))
    newlist.sort()
    # begin string
    string = str(newlist[0])
    # iteration through list:
    dash = False
    for i in np.arange(len(newlist)-1)+1:
        if dash == True:
            if newlist[i]-1 == newlist[i-1]:
                pass
            else:
                string += "-"+str(newlist[i-1])+", "+str(newlist[i])
                dash = False
        else:
            if newlist[i]-1 == newlist[i-1]:
                if newlist[i]-2 == newlist[i-2]:
                    dash = True
                elif len(newlist) != i+1 and newlist[i]+1 == newlist[i+1]:
                    dash = True
                else:
                    string += ", "+str(newlist[i])
                    dash = False
            else:
                dash = False
                string += ", "+str(newlist[i])
        # Put final number
        if newlist[i] == newlist[-1]:
            if parseString2Pagenum(None, string)[-1] != newlist[i]:
                if dash == True:
                    string += "-"+str(newlist[i])
                else:
                    string += ", "+str(newlist[i])
    return string


def removewrongUTF8(name):
    newname = u""
    for char in name:
        try:
            codecs.decode(char, "UTF-8")
        except:
            pass
        else:
            newname += char
    return newname


def getMainIcon(pxlength=32):
    """ *pxlength* is the side length in pixels of the icon """
    # Set window icon
    iconBMP = icon.getMainBitmap()
    # scale
    image = wx.Bitmap.ConvertToImage(iconBMP)
    image = image.Scale(pxlength, pxlength, wx.IMAGE_QUALITY_HIGH)
    iconBMP = wx.Bitmap(image)
    iconICO = wx.Icon(iconBMP)
    return iconICO
