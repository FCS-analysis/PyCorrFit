# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - batch
    Stuff that concerns batch processing.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³

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


import numpy as np
import wx

import openfile as opf     # How to treat an opened file
import models as mdls

# Menu entry name
MENUINFO = ["B&atch control", "Batch fitting."]

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
        self.panel = panel
        text1 = wx.StaticText(panel, label="Choose source of parameters:")
        self.rbtnhere = wx.RadioButton(panel, -1, 'This session', 
                                        style = wx.RB_GROUP)
        self.rbtnhere.SetValue(True)
        self.rbtnthere = wx.RadioButton(panel, -1, 'Other session')
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
        self.SetMinSize(topSizer.GetMinSizeTuple())
        # Check if we even have pages.
        self.OnPageChanged()
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
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
            if OtherPage.modelid == modelid and OtherPage.dataexp is not None:
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
                OtherPage.Fit_function(noplots=True)


    def OnPageChanged(self, Page=None):
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        else:
            self.panel.Enable()
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
