# -*- coding: utf-8 -*-
""" PyCorrFit

    EditedClasses
    Contains classes that we edited.
    Should make our classes more useful.

    Copyright (C) 2011-2012  Paul Müller

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License 
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


# Matplotlib plotting capabilities
try:
    import matplotlib
except ImportError:
    pass
# We do catch warnings about performing this before matplotlib.backends stuff
#matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        matplotlib.use('WXAgg') # Tells matplotlib to use WxWidgets for dialogs
    except:
        pass
# We will hack this toolbar here
try:
    from matplotlib.backends.backend_wx import NavigationToolbar2Wx 
except ImportError:
    pass
    
import numpy as np
import sys
import traceback
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx 


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
        #super(ChoicesDialog, self).__init__(parent=parent, 
        #    title=title)
        wx.Dialog.__init__(self, parent, -1, title)
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
        #self.Show(True)
        self.SetFocus()

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
    dlg = wx.FileDialog(parent, "Save figure", dirname, filename, 
           fieltypestring, wx.SAVE|wx.OVERWRITE_PROMPT)
    # png is default
    dlg.SetFilterIndex(keys.index("png"))
    # user cannot do anything until he clicks "OK"
    if dlg.ShowModal() == wx.ID_OK:
        wildcard = keys[dlg.GetFilterIndex()]
        filename = dlg.GetPath()
        haswc = False
        for key in keys:
            if filename.lower().endswith("."+key) is True:
                haswc = True
        if haswc == False:
            filename = filename+"."+wildcard
        dirname = dlg.GetDirectory()
        #savename = os.path.join(dirname, filename)
        savename = filename
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
            wx.MessageDialog(parent, errstr, "Error", 
                style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
    else:
        dirname = dlg.GetDirectory()
    try:
        parent.dirname = dirname
    except:
        pass


class MyScrolledDialog(wx.Dialog):
    def __init__(self, parent, overtext, readtext, title):
        wx.Dialog.__init__(self, parent, title=title)
        overtext = wx.StaticText(self, label=overtext)
        text = wx.TextCtrl(self, -1, readtext, size=(500,400),
                           style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer = wx.BoxSizer(wx.VERTICAL )
        btnsizer = wx.BoxSizer()
        btn = wx.Button(self, wx.ID_OK)#, "OK ")
        btnsizer.Add(btn, 0, wx.ALL, 5)
        btnsizer.Add((5,-1), 0, wx.ALL, 5)
        btn = wx.Button(self, wx.ID_CANCEL)#, "Abort ")
        btnsizer.Add(btn, 0, wx.ALL, 5)
        sizer.Add(overtext, 0, wx.EXPAND|wx.ALL, 5)   
        sizer.Add(text, 0, wx.EXPAND|wx.ALL, 5)   
        sizer.Add(btnsizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)   
        self.SetSizerAndFit(sizer)
        
        
class MyOKAbortDialog(wx.Dialog):
    def __init__(self, parent, text, title):
        wx.Dialog.__init__(self, parent, title=title)
        overtext = wx.StaticText(self, label=text)
        sizer = wx.BoxSizer(wx.VERTICAL )
        btnsizer = wx.BoxSizer()
        btn = wx.Button(self, wx.ID_OK)#, "OK ")
        btnsizer.Add(btn, 0, wx.ALL, 5)
        btnsizer.Add((5,-1), 0, wx.ALL, 5)
        btn = wx.Button(self, wx.ID_CANCEL)#, "Abort ")
        btnsizer.Add(btn, 0, wx.ALL, 5)
        sizer.Add(overtext, 0, wx.EXPAND|wx.ALL, 5)   
        sizer.Add(btnsizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)   
        self.SetSizerAndFit(sizer)
        
        
class MyYesNoAbortDialog(wx.Dialog):
    def __init__(self, parent, text, title):
        wx.Dialog.__init__(self, parent, title=title)
        overtext = wx.StaticText(self, label=text)
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnsizer = wx.BoxSizer()
        btn1 = wx.Button(self, wx.ID_YES)
        #btn1.Bind(wx.EVT_BTN, self.YES)
        btnsizer.Add(btn1, 0, wx.ALL, 5)
        btnsizer.Add((1,-1), 0, wx.ALL, 5)
        btn2 = wx.Button(self, wx.ID_NO)
        btnsizer.Add(btn2, 0, wx.ALL, 5)
        btnsizer.Add((1,-1), 0, wx.ALL, 5)
        btn3 = wx.Button(self, wx.ID_CANCEL)
        btnsizer.Add(btn3, 0, wx.ALL, 5)
        sizer.Add(overtext, 0, wx.EXPAND|wx.ALL, 5)   
        sizer.Add(btnsizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)   
        self.SetSizerAndFit(sizer)
        self.SetFocus()
        self.Show()
        
    def YES(self, e):
        self.EndModal(wx.ID_YES)


try:
    # Add the save_figure function to the standard class for wx widgets.
    matplotlib.backends.backend_wx.NavigationToolbar2Wx.save = save_figure
except (NameError, AttributeError):
    pass
