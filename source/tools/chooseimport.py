# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - chooseimport
    Displays a window that lets the user choose what type
    of data (AC1, AC2, CC12, CC21) he wants to import.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""

# We may import different things from throughout the program:
import wx
import numpy as np
import models as mdls
import doc

class ChooseImportTypes(wx.Dialog):
    # This tool is derived from a wx.frame.
    def __init__(self, parent, curvedict):
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # init
        super(ChooseImportTypes, self).__init__(parent=parent, 
            title="Choose types", size=(250, 200))

        self.keys = list()
         ## Content
        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.boxes = dict()

        textinit = wx.StaticText(self.panel, label=doc.chooseimport)
        self.sizer.Add(textinit)
        thekeys = curvedict.keys()
        thekeys.sort()

        for key in thekeys:
            label = key + " (" + str(len(curvedict[key])) + " curves)"
            check = wx.CheckBox(self.panel, label=label)
            self.boxes[key] = check
            self.sizer.Add(check)
            self.Bind(wx.EVT_CHECKBOX, self.OnSetkeys, check)


        btnok = wx.Button(self.panel, wx.ID_OK, 'OK')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnClose, btnok)
       
        self.sizer.Add(btnok)

        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.Show(True)

    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.EndModal(wx.ID_OK)
        #self.Show
        #self.Destroy()

    def OnSetkeys(self, event = None):
        self.keys = list()
        for key in self.boxes.keys():
            if self.boxes[key].Value == True:
                self.keys.append(key)

class ChooseImportTypesModel(wx.Dialog):
    # This tool is derived from a wx.frame.
    def __init__(self, parent, curvedict):
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # init
        super(ChooseImportTypesModel, self).__init__(parent=parent, 
            title="Choose types", size=(250, 200))

        self.curvedict = curvedict
        self.keys = list()
        # Dictionary of modelids corresponding to indices in curvedict
        self.modelids = dict()
         ## Content
        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.boxes = dict()

        textinit = wx.StaticText(self.panel, label=doc.chooseimport)
        self.sizer.Add(textinit)
        thekeys = curvedict.keys()
        thekeys.sort()

        for key in thekeys:
            label = key + " (" + str(len(curvedict[key])) + " curves)"
            check = wx.CheckBox(self.panel, label=label)
            self.boxes[key] = check
            self.sizer.Add(check)
            self.Bind(wx.EVT_CHECKBOX, self.OnSetkeys, check)


        btnok = wx.Button(self.panel, wx.ID_OK, 'OK')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnClose, btnok)
       
        self.sizer.Add(btnok)

        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.Show(True)

    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.EndModal(wx.ID_OK)
        #self.Show
        #self.Destroy()

    def OnSetkeys(self, event = None):
        self.keys = list()
        for key in self.boxes.keys():
            if self.boxes[key].Value == True:
                self.keys.append(key)
        self.modelids = dict()
        for key in self.curvedict.keys():
            if self.boxes[key].Value == True:
                for index in self.curvedict[key]:
                    # Set different model id for the curves
                    self.modelids[index] = 6000
