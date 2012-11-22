# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    EditedClasses
    Contains classes that we edited.
    Should make our classes more useful.

"""

# Making different sized subplots
import matplotlib
matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets
from matplotlib.backends.backend_wx import NavigationToolbar2Wx #We hack this
import numpy as np
import os
import sys
import traceback
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx 

import platform








class FloatSpin(floatspin.FloatSpin):
    def __init__(self, parent, digits=10, increment=.01):
        floatspin.FloatSpin.__init__(self, parent, digits=digits,
                                     increment = increment)
        self.Bind(wx.EVT_SPINCTRL, self.increment)
        #self.Bind(wx.EVT_SPIN, self.increment)
        #self.increment()

    def increment(self, event=None):
        # Find significant digit
        # and use it as the new increment
        x = self.GetValue()
        if x == 0:
            incre = 0.1
        else:
            digit = int(np.ceil(np.log10(abs(x)))) - 2
            incre = 10**digit
        self.SetIncrement(incre)


class ChoicesDialog(wx.Dialog):
    def __init__(self, parent, dropdownlist, title, text):
        # parent is main frame
        self.parent = parent

        super(ChoicesDialog, self).__init__(parent=parent, 
            title=title)
        # Get the window positioning correctly
        #pos = self.parent.GetPosition()
        #pos = (pos[0]+100, pos[1]+100)
        #wx.Frame.__init__(self, parent=parent, title=title,
        #         pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)

        #self.Filename = None
        ## Controls
        panel = wx.Panel(self)

        # text1
        textopen = wx.StaticText(panel, label=text)
        btnok = wx.Button(panel, wx.ID_OK)
        btnabort = wx.Button(panel, wx.ID_CANCEL)

        # Dropdown
        self.dropdown = wx.ComboBox(panel, -1, "", (15, 30),
              wx.DefaultSize, dropdownlist, wx.CB_DROPDOWN|wx.CB_READONLY)
        self.dropdown.SetSelection(0)
        # Bindings
        self.Bind(wx.EVT_BUTTON, self.OnOK, btnok)
        self.Bind(wx.EVT_BUTTON, self.OnAbort, btnabort)

        # Sizers
        topSizer = wx.BoxSizer(wx.VERTICAL)

        topSizer.Add(textopen)
        topSizer.Add(self.dropdown)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(btnok)
        btnSizer.Add(btnabort)

        topSizer.Add(btnSizer)

        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.Show(True)

    def OnOK(self, event=None):
        self.SelcetedID = self.dropdown.GetSelection()
        self.EndModal(wx.ID_OK)

    def OnAbort(self, event=None):
        self.EndModal(wx.ID_CANCEL)



def save_figure(self, evt=None):
    """
        A substitude function for save in:
        matplotlib.backends.backend_wx.NavigationToolbar2Wx
        We want to be able to give parameters such as dirname and filename.
    """
    try:
        parent=self.canvas.HACK_parent
        fig=self.canvas.HACK_fig
        Page = self.canvas.HACK_Page
        add = self.canvas.HACK_append
        dirname = parent.dirname
        filename = Page.tabtitle.GetValue().strip()+Page.counter[:2]+add
        formats = fig.canvas.get_supported_filetypes()
    except:
        dirname = "."
        filename = ""
        formats = self.canvas.get_supported_filetypes()
        parent = self

    fieltypestring = ""
    keys = formats.keys()
    keys.sort()
    for key in keys:
        fieltypestring += formats[key]+"(*."+key+")|*."+key+"|"
    # remove last |
    fieltypestring = fieltypestring[:-1]
    dlg = wx.FileDialog(parent, "Choose a data file", dirname, filename, 
           fieltypestring, wx.SAVE|wx.OVERWRITE_PROMPT)

    # png is default
    dlg.SetFilterIndex(keys.index("png"))

    # user cannot do anything until he clicks "OK"
    if dlg.ShowModal() == wx.ID_OK:
        wildcard = keys[dlg.GetFilterIndex()]
        filename = dlg.GetFilename()
        haswc = False
        for key in keys:
            if filename.lower().endswith("."+key) is True:
                haswc = True
        if haswc == False:
            filename = filename+"."+wildcard
        dirname = dlg.GetDirectory()
        savename = os.path.join(dirname, filename)

        try:
            self.canvas.figure.savefig(savename)
        except: # RuntimeError:
            # The file does not seem to be what it seems to be.
            info = sys.exc_info()
            errstr = "Could not latex output:\n"
            errstr += str(filename)+"\n\n"
            errstr += str(info[0])+"\n"
            errstr += str(info[1])+"\n"
            for tb_item in traceback.format_tb(info[2]):
                errstr += tb_item
            dlg3 = wx.MessageDialog(parent, errstr, "Error", 
                style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
            dlg3.ShowModal() == wx.ID_OK
    try:
        parent.dirname = dirname
    except:
        pass
#plt.close()
NavigationToolbar2Wx.save = save_figure

