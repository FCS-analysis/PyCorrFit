# -*- coding: utf-8 -*-
""" 
PyCorrFit

Module tools - batch
Stuff that concerns batch processing.
"""


import numpy as np
import os
import wx

from .. import openfile as opf     # How to treat an opened file
from .. import models as mdls


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
            if OtherPage.corr.fit_model.id == modelid and OtherPage.corr.correlation is not None:
                self.parent.UnpackParameters(Parms, OtherPage)
                OtherPage.PlotAll(trigger="parm_batch")
        # Update all other tools fit the finalize trigger.
        self.parent.OnFNBPageChanged(trigger="parm_finalize")


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
                Page = self.parent.notebook.GetPage(item-1)
            # Get internal ID
            modelid = Page.corr.fit_model.id
        else:
            # Get external ID
            modelid = self.YamlParms[item][1]
        # Fit all pages with right modelid
        for i in np.arange(self.parent.notebook.GetPageCount()):
            OtherPage = self.parent.notebook.GetPage(i)
            if (OtherPage.corr.fit_model.id == modelid and
                OtherPage.corr.correlation is not None):
                #Fit
                OtherPage.Fit_function(noplots=True,trigger="fit_batch")
        # Update all other tools fit the finalize trigger.
        self.parent.OnFNBPageChanged(trigger="fit_finalize")


    def OnPageChanged(self, Page=None, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        else:
            self.panel.Enable()
        # Filter triggers
        if trigger in ["fit_batch", "fit_finalize",
                       "parm_batch", "parm_finalize"]:
            return
        # We need to update the list of Pages in self.dropdown
        if self.rbtnhere.Value == True:
            DDlist = list()
            DDlist.append("Current page")
            for i in np.arange(self.parent.notebook.GetPageCount()):
                aPage = self.parent.notebook.GetPage(i)
                DDlist.append(aPage.counter+aPage.tabtitle.GetValue())
            self.dropdown.SetItems(DDlist)
            self.dropdown.SetSelection(0)


    def OnRadioHere(self, event=None):
        self.OnPageChanged(trigger="view")


    def OnRadioThere(self, event=None):
        # If user clicks on pages in main program, we do not want the list
        # to be changed.
        wc = opf.session_wildcards
        wcstring = "PyCorrFit session (*.pcfs)|*{};*{}".format(
                                                           wc[0], wc[1])
        dlg = wx.FileDialog(self.parent, "Open session file",
                            self.parent.dirname, "", wcstring, wx.FD_OPEN)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            sessionfile = dlg.GetPath()
            self.dirname = os.path.split(sessionfile)[0]
        else:
            self.parent.dirname=dlg.GetDirectory()
            self.rbtnhere.SetValue(True)
            return

        Infodict = opf.LoadSessionData(sessionfile,
                                       parameters_only=True)
        self.YamlParms = Infodict["Parameters"]
        DDlist = list()
        for i in np.arange(len(self.YamlParms)):
            # Rebuild the list
            modelid = self.YamlParms[i][1]
            modelname = mdls.modeldict[modelid][1]
            DDlist.append(self.YamlParms[i][0]+modelname)
        self.dropdown.SetItems(DDlist)
        # Set selection text to first item
        self.dropdown.SetSelection(0)
