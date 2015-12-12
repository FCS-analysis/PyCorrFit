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
        ## Misc
        try:
            self.curpage = self.parent.notebook.GetCurrentPage()
        except:
            self.curpage = None
        ## Controls
        panel = wx.Panel(self)
        self.panel = panel
        #Icon
        self.Redraw()
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)

    
    def GetParameters(self):
        """ The parameters
        """
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
        return Parms


    def GetProtectedParameterIDs(self):
        """ The model parameters that are protected from batch control
        
        """
        pbool = [ not cb.GetValue() for cb in self.wxParameterCheckBoxes ]
        return np.array(pbool, dtype=bool)
    
    
    def OnApply(self, event):
        Parms = self.GetParameters()
        modelid = Parms[1]
        # Set all parameters for all pages
        for i in np.arange(self.parent.notebook.GetPageCount()):
            OtherPage = self.parent.notebook.GetPage(i)
            if (OtherPage.corr.fit_model.id == modelid and
                OtherPage.corr.correlation is not None):
                # create a copy of the fitting parameters in
                # case we want to protect them
                proparms = OtherPage.corr.fit_parameters
                self.parent.UnpackParameters(Parms, OtherPage)
                if OtherPage.prevent_batch_modification:
                    # write back protected parameters
                    OtherPage.corr.fit_parameters = proparms
                else:
                    # write back only selected parameters
                    pbool = self.GetProtectedParameterIDs()
                    OtherPage.corr.fit_parameters[pbool] = proparms[pbool]
                OtherPage.apply_parameters_reverse()
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
            # nothing to do
            return
        else:
            self.panel.Enable()
        # Filter triggers
        if trigger in ["fit_batch", "fit_finalize", "init",
                       "parm_batch", "parm_finalize"]:
            return
        
        if Page is not None:
            # redraw this tool if necessary
            if self.curpage is not None:
                oldmodelid = self.curpage.modelid
            else:
                oldmodelid = 0
            newmodelid = Page.modelid
            if oldmodelid != newmodelid:
                self.RedrawParameterBox()

        # We need to update the list of Pages in self.dropdown
        if self.rbtnhere.Value == True:
            DDlist = list()
            DDlist.append("Current page")
            for i in np.arange(self.parent.notebook.GetPageCount()):
                aPage = self.parent.notebook.GetPage(i)
                DDlist.append(aPage.counter+aPage.tabtitle.GetValue())
            self.dropdown.SetItems(DDlist)
            self.dropdown.SetSelection(0)

        self.curpage = self.parent.notebook.GetCurrentPage()


    def OnRadioHere(self, event=None):
        self.OnPageChanged(trigger="view")
        self.RedrawParameterBox()


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
        self.RedrawParameterBox()


    def Redraw(self, e=None):
        panel = self.panel
        for child in panel.GetChildren():
            panel.RemoveChild(child)
            child.Destroy()

        ## Parameter source selection
        boxleft = wx.StaticBox(panel, label="Parameter source")
        self.rbtnhere = wx.RadioButton(panel, -1, 'This session', 
                                        style = wx.RB_GROUP)
        self.rbtnhere.SetValue(True)
        self.rbtnthere = wx.RadioButton(panel, -1, 'Other session')
        self.dropdown = wx.ComboBox(panel, -1, "Current page", (15, 30),
                         wx.DefaultSize, [], wx.CB_DROPDOWN|wx.CB_READONLY)
        # Create the dropdownlist
        text2 = wx.StaticText(panel, label="""Only data sets that have the
same model as the parameter
source will be affected by
batch modification, which
includes parameter values as
well as settings for fitting
and background correction.
To prevent batch modification
of parameter values for an
individual page, check its 
"prevent batch modification"
check box.""")
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioHere, self.rbtnhere)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioThere, self.rbtnthere)
        self.Bind(wx.EVT_COMBOBOX, self.RedrawParameterBox, self.dropdown)
        leftSizer = wx.StaticBoxSizer(boxleft, wx.VERTICAL)
        leftSizer.Add(self.rbtnhere)
        leftSizer.Add(self.rbtnthere)
        leftSizer.AddSpacer(5)
        leftSizer.Add(self.dropdown)
        leftSizer.AddSpacer(5)
        leftSizer.Add(text2)
        leftSizer.AddSpacer(5)

        ## Parameter selection
        boxright = wx.StaticBox(panel, label="Selected parameters")
        rightSizer = wx.StaticBoxSizer(boxright, wx.VERTICAL)
        boxright.SetSizer(rightSizer)
        self.parameter_sizer = rightSizer
        self.RedrawParameterBox()

        ## Buttons
        btnapply = wx.Button(panel, wx.ID_ANY, 'Apply to applicable pages')
        btnfit = wx.Button(panel, wx.ID_ANY, 'Fit applicable pages')
        # Bindings
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnapply)
        self.Bind(wx.EVT_BUTTON, self.OnFit, btnfit)

        ## Sizers
        sizer_bag = wx.GridBagSizer(hgap=5, vgap=5)
        sizer_bag.Add(leftSizer, (0,0))
        sizer_bag.Add(rightSizer, (0,1))
        horsizer = wx.BoxSizer(wx.HORIZONTAL)
        horsizer.Add(btnapply)
        horsizer.Add(btnfit)
        sizer_bag.Add(horsizer, (1,0), span=wx.GBSpan(1,2))
        
        panel.SetSizer(sizer_bag)
        sizer_bag.Fit(panel)
        self.SetMinSize(sizer_bag.GetMinSizeTuple())
        # Check if we even have pages.
        self.OnPageChanged()
        panel.Layout()
        sizer_bag.Fit(self)
        self.mastersizer = sizer_bag
        

    def RedrawParameterBox(self, e=None):
        sizer = self.parameter_sizer
        panel = self.panel
        for child in sizer.GetChildren():
            window = child.GetWindow()
            panel.RemoveChild(window)
            sizer.RemoveWindow(window)
            window.Destroy()

        text = wx.StaticText(panel, label="""If desired, (de)select
individual parameters
for batch modification.""")
        sizer.Add(text)

        if self.parent.notebook.GetPageCount():
            # Get parameters of current page
            parms = self.GetParameters()
            modelid = parms[1]
            ptext, _pval = mdls.GetHumanReadableParms(modelid, parms[2])
            ptext = [ p.split()[0] for p in ptext ]
            self.wxParameterCheckBoxes = []
            for p in ptext:
                cb = wx.CheckBox(panel, label=p)
                cb.SetValue(True)
                self.wxParameterCheckBoxes.append(cb)
                sizer.Add(cb)

        # Try to set sizes correctly
        box = sizer.GetStaticBox()
        boxs = box.GetBestSize()
        sizs = sizer.GetMinSize()
        thesize = (max(boxs[0], sizs[0]+20), sizs[1])
        sizer.SetMinSize(thesize)
        box.SetMinSize(thesize)
        box.SetSize(thesize)

        try:
            self.mastersizer.Fit(panel)
            panel.Layout()
            self.SetSize(panel.GetSize())
        except:
            pass