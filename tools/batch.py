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
import sys
import traceback                        # for Error handling
import wx

import openfile as opf                     # How to treat an opened file
import models as mdls

import platform
if platform.system() == 'Linux':
    from IPython.Shell import IPythonShellEmbed
    ipshell = IPythonShellEmbed()
   #ipshell()

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
            if OtherPage.modelid == modelid and OtherPage.dataexpfull is not None:
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
        self.YamlParms, dirname, filename = opf.ImportParametersYaml(self.parent, 
                                                             self.parent.dirname)
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


class BatchImport(wx.Frame):
    def __init__(self, parent):
        # parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=parent, title="Batch import",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)

        self.Filenames = None
        ## Controls
        panel = wx.Panel(self)

        # text1
        textopen = wx.StaticText(panel, label="Choose data files: ")
        self.btnbrowse = wx.Button(panel, wx.ID_ANY, 'Browse ...')

        self.textfile = wx.StaticText(panel, label="No files selected.")


        # Dropdown
        textdropdown = wx.StaticText(panel, label="Select model: ")
        # The list for the dropdown
        self.ModelDropdown = list()
        # A list with all the models in the same order as in self.ModelDropdown
        self.modellist = list()
        # Use the key to label each available model
        keys = mdls.modeltypes.keys()
        keys.sort()
        for modeltype in keys:
            for modelid in mdls.modeltypes[modeltype]:
                self.ModelDropdown.append(modeltype + ": "+ mdls.modeldict[modelid][1])
                self.modellist.append(mdls.modeldict[modelid])

            
        self.dropdown = wx.ComboBox(panel, -1, "Select model", (15, 30),
              wx.DefaultSize, self.ModelDropdown, wx.CB_DROPDOWN|wx.CB_READONLY)


        # name
        textname = wx.StaticText(panel, label="Custom name: ")
        self.modname = wx.TextCtrl(panel, value="", size=(240,-1))
        self.modname.Enable(False)

        self.btnimport = wx.Button(panel, wx.ID_ANY, 'Import into session')
        self.btnimport.Enable(False)

        # Bindings
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.btnbrowse)
        self.Bind(wx.EVT_BUTTON, self.OnImport, self.btnimport)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelModel, self.dropdown)

        # Sizers
        topSizer = wx.BoxSizer(wx.VERTICAL)

        text1sizer = wx.BoxSizer(wx.HORIZONTAL)
        text1sizer.Add(textopen)
        text1sizer.Add(self.btnbrowse)

        dropsizer = wx.BoxSizer(wx.HORIZONTAL)
        dropsizer.Add(textdropdown)
        dropsizer.Add(self.dropdown)

        namesizer = wx.BoxSizer(wx.HORIZONTAL)
        namesizer.Add(textname)
        namesizer.Add(self.modname)

        topSizer.Add(text1sizer)
        topSizer.Add(self.textfile)
        topSizer.Add(dropsizer)
        topSizer.Add(namesizer)
        topSizer.Add(self.btnimport)

        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.Show(True)
        #psize = panel.GetBestSize()
        #self.SetSize(psize)


    def CheckIfImportOK(self):
        if self.Filenames is not None and self.dropdown.GetSelection() != -1:
            self.btnimport.Enable(True)

    def OnBrowse(self, event):
        SupFiletypes = opf.Filetypes.keys()
        # Sort them so we have "All suported filetypes" up front
        SupFiletypes.sort()
        filters = ""
        for i in np.arange(len(SupFiletypes)):
            # Add to the filetype filter
            filters = filters+SupFiletypes[i]
            if i+1 != len(SupFiletypes):
                # Add a separator if item is not last item
                filters = filters+"|"
        dlg = wx.FileDialog(self.parent, "Choose a data file", 
            self.parent.dirname, "", filters, wx.OPEN|wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.Filenames = dlg.GetFilenames()
            filterindex = dlg.GetFilterIndex()
            self.Filetype = SupFiletypes[filterindex]
            self.textfile.SetLabel(str(len(self.Filenames))+" files selected.")
            self.CheckIfImportOK()
        self.parent.dirname = dlg.GetDirectory()
        dlg.Destroy()

    def OnSelModel(self, event):
        item = self.dropdown.GetSelection()
        self.SelectedModelID = self.modellist[item][0]
        self.CheckIfImportOK()
        self.modname.Enable(True)

    def OnImport(self, event):
        dirname = self.parent.dirname
        # Define which function we should use for opening, depending on the user
        # selected wildcard in the file dialog.
        OpenFile = opf.Filetypes[self.Filetype]
        numf = len(self.Filenames)
        # Show a nice progress dialog:
        style=wx.PD_REMAINING_TIME|wx.PD_SMOOTH|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT
        dlga = wx.ProgressDialog("Import", "Loading pages..."
        , maximum = numf, parent=self, style=style)
        for i in np.arange(numf):
            # Let the user abort, if he wants to:
            if dlga.Update(i+1, "Loading pages...")[0] == False:
                dlga.Destroy()
                return
            filename = self.Filenames[i]
            self.parent.filename = filename
            self.parent.add_fitting_tab(modelid=self.SelectedModelID)
            # Now insert user information, data, etc.
            try:
                Stuff = OpenFile(dirname, filename)
            except:
                # The file does not seem to be what it seems to be.
                info = sys.exc_info()
                errstr = "Unknown file format:\n"
                errstr += str(filename)+"\n\n"
                errstr += str(info[0])+"\n"
                errstr += str(info[1])+"\n"
                for tb_item in traceback.format_tb(info[2]):
                    errstr += tb_item
                dlg = wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg.ShowModal() == wx.ID_OK
                dlga.Destroy()
                return
            else:
                dataexp = Stuff[0]
                trace = Stuff[1]
                curvelist = Stuff[2]
                # If curvelist is a list with more than one item, we are
                # importing more than one curve per file. Therefore, we
                # need to create more pages for this file.
                # curvelist is a list of numbers or labels that correspond
                # to each item in dataexp or trave. Each curvlist item
                # will be converted to a string and then added to the
                # pages title.
                num = len(curvelist) 
                for j in np.arange(num):
                    # Fill Page with data
                    CurPage = self.parent.notebook.GetCurrentPage()
                    CurPage.filename = filename+" "+str(curvelist[j])
                    self.parent.ImportData(dataexp[j], trace[j], curvelist[j])
                    if j+1 != num:
                        # Create new Page.
                        # Add n-1 pages while importing.
                        self.parent.add_fitting_tab(event=None, 
                                             modelid=CurPage.modelid,
                                             counter=None)
                    # Set the title according to the user input
                    titlestring=CurPage.filename+" "+self.modname.GetValue()
                    # Strip leading or trailing white spaces.
                    CurPage.tabtitle.SetValue(titlestring.strip())
                # Do not put a return here. We still have a for-loop running.

