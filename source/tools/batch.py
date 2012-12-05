# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - batch
    Stuff that concerns batch processing.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


import numpy as np
import platform
import sys
import traceback           # for Error handling
import wx

# PyCorrFit modules
import openfile as opf     # How to treat an opened file
import models as mdls


class BatchCtrl(wx.Frame):
    def __init__(self, parent):
        # Parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=parent, title="Batch control",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None

        ## Controls
        panel = wx.Panel(self)

        text1 = wx.StaticText(panel, label="Choose source of parameters:")
        self.rbtnhere = wx.RadioButton (panel, -1, 'This session', 
                                        style = wx.RB_GROUP)
        self.rbtnthere = wx.RadioButton (panel, -1, 'Other session')

        self.dropdown = wx.ComboBox(panel, -1, "Current page", (15, 30),
                         wx.DefaultSize, [], wx.CB_DROPDOWN|wx.CB_READONLY)
        # Create the dropdownlist
        self.OnPageChanged()
        text2 = wx.StaticText(panel, label='This will affect all pages'+
                                           '\nwith the same model.'+
                                           '\nApply parameters:')
        btnapply = wx.Button(panel, wx.ID_ANY, 'Apply to applicable pages')
        btnfit = wx.Button(panel, wx.ID_ANY, 'Fit applicable pages')

        # Bindings
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnapply)
        self.Bind(wx.EVT_BUTTON, self.OnFit, btnfit)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioHere, self.rbtnhere)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioThere, self.rbtnthere)
        # self.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.dropdown)

        topSizer = wx.BoxSizer(wx.VERTICAL)

        topSizer.Add(text1)
        topSizer.Add(self.rbtnhere)
        topSizer.Add(self.rbtnthere)
        topSizer.AddSpacer(5)
        topSizer.Add(self.dropdown)
        topSizer.AddSpacer(5)
        topSizer.Add(text2)
        topSizer.AddSpacer(5)
        topSizer.Add(btnapply)
        topSizer.Add(btnfit)

        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.Show(True)

    def OnApply(self, event):
        # Get the item from the dropdown list
        item = self.dropdown.GetSelection()
        if self.rbtnhere.Value == True:
            # Get parameters from this session
            if item <= 0:
                Page = self.parent.notebook.GetCurrentPage()
            else:
                Page = self.parent.notebook.GetPage(item-1)
            # First apply the parameters of the page
            Page.apply_parameters()          
            # Get all parameters
            Parms = self.parent.PackParameters(Page)
        else:
            # Get Parameters from different session
            Parms = self.YamlParms[item]

        modelid = Parms[1]
        # Set all parameters for all pages
        for i in np.arange(self.parent.notebook.GetPageCount()):
            OtherPage = self.parent.notebook.GetPage(i)
            if OtherPage.modelid == modelid:
                self.parent.UnpackParameters(Parms, OtherPage)
                OtherPage.PlotAll()

    def OnClose(self, event=None):
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()

    def OnFit(self, event):
        item = self.dropdown.GetSelection()
        if self.rbtnhere.Value == True:
            if item <= 0:
                Page = self.parent.notebook.GetCurrentPage()
            else:
                Page = self.parent.notebook.GetPage(item)
            # Get internal ID
            modelid = Page.modelid
        else:
            # Get external ID
            modelid = self.YamlParms[item][1]
        # Fit all pages with right modelid
        for i in np.arange(self.parent.notebook.GetPageCount()):
            OtherPage = self.parent.notebook.GetPage(i)
            if (OtherPage.modelid == modelid and
                OtherPage.dataexpfull is not None):
                #Fit
                OtherPage.Fit_function()

    def OnPageChanged(self, Page=None):
        # We need to update the list of Pages in self.dropdown
        if self.rbtnhere.Value == True:
            DDlist = list()
            DDlist.append("Current page")
            for i in np.arange(self.parent.notebook.GetPageCount()):
                aPage = self.parent.notebook.GetPage(i)
                DDlist.append(aPage.counter+aPage.model)
            self.dropdown.SetItems(DDlist)
            self.dropdown.SetSelection(0)

    def OnRadioHere(self, event=None):
        self.OnPageChanged()

    def OnRadioThere(self, event=None):
        # If user clicks on pages in main program, we do not want the list
        # to be changed.
        self.YamlParms, dirname, filename = \
                      opf.ImportParametersYaml(self.parent, self.parent.dirname)
        if filename == None:
            # User did not select any sesion file
            self.rbtnhere.SetValue(True)
        else:
            DDlist = list()
            for i in np.arange(len(self.YamlParms)):
                # Rebuild the list
                modelid = self.YamlParms[i][1]
                modelname = mdls.modeldict[modelid][1]
                DDlist.append(self.YamlParms[i][0]+modelname)
            self.dropdown.SetItems(DDlist)
            # Set selection text to first item
            self.dropdown.SetSelection(0)