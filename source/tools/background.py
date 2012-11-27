# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - background
    We make some background corection here.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""

# python modules
import numpy as np
import sys
import traceback                        # for Error handling
import wx
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx.lib.plot as plot    

# PyCorrFit modules
import doc
import openfile as opf                  # How to treat an opened file
import readfiles

class BackgroundCorrection(wx.Frame):
    def __init__(self, parent):
        # Parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=parent, title="Background correction",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        

        # Current trace we are looking at
        self.activetrace = None 
        # Importet trace
        self.trace = None
        # Importet trace after user decides to cange radio buttons
        self.oldtrace = None
        self.oldfilename = None
        self.average = None
        ## Start drawing
        # Splitter Window
        self.sp = wx.SplitterWindow(self, style=wx.SP_NOBORDER)


        ## Controls
        panel = wx.Panel(self.sp)

        # text1
        textinit = wx.StaticText(panel, label=doc.backgroundinit)
        # Radio buttons
        self.rbtnfile = wx.RadioButton (panel, -1, 'Blank measurement: ', 
                                        style = wx.RB_GROUP)
        self.btnbrowse = wx.Button(panel, wx.ID_ANY, 'Browse ...')
        self.rbtnhand = wx.RadioButton (panel, -1, 'Manual, <B> [kHz]: ')
        # Spincontrol
        self.spinctrl = floatspin.FloatSpin(panel, digits=7,
                                            increment=.1)
        self.spinctrl.Enable(False)
        # Verbose text
        self.textfile = wx.StaticText(panel,
                                    label="No blank measurement file selected.")
        textmeanavg = wx.StaticText(panel,
                                    label="Average background signal [kHz]: ")
        self.textmean = wx.StaticText(panel, label="")

        # name
        textname = wx.StaticText(panel, label="User defined background name: ")
        self.bgname = wx.TextCtrl(panel, value="", size=(330,-1))
        self.bgname.Enable(False)

        self.btnimport = wx.Button(panel, wx.ID_ANY, 'Import into session')
        self.btnimport.Enable(False)


        # Dropdown
        textdropdown = wx.StaticText(panel, label="Show background: ")
        self.BGlist = list()
        self.BGlist.append("File/User")
        for item in self.parent.Background:
            self.BGlist.append(item[1])
        self.dropdown = wx.ComboBox(panel, -1, "File/User", (15, 30),
                     wx.DefaultSize, self.BGlist, wx.CB_DROPDOWN|wx.CB_READONLY)
        self.textafterdropdown = wx.StaticText(panel, label="")

        # Apply buttons
        textapply = wx.StaticText(panel, label="Apply background to: ")
        self.btnapply = wx.Button(panel, wx.ID_ANY, 'Current page only')
        self.btnapplyall = wx.Button(panel, wx.ID_ANY, 'All pages')
        self.btnapply.Enable(False)
        self.btnapplyall.Enable(False)

        # Remove Backgrounds
        textrem = wx.StaticText(panel, label="Remove background from: ")
        self.btnrem = wx.Button(panel, wx.ID_ANY, 'Current page only')
        self.btnremyall = wx.Button(panel, wx.ID_ANY, 'All pages')
        if len(self.BGlist) <= 1:
            self.btnrem.Enable(False)
            self.btnremyall.Enable(False)

        # Bindings
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.btnbrowse)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioFile, self.rbtnfile)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioHand, self.rbtnhand)
        self.Bind(wx.EVT_SPINCTRL, self.SpinCtrlChange, self.spinctrl)
        self.Bind(wx.EVT_BUTTON, self.OnImport, self.btnimport)
        self.Bind(wx.EVT_COMBOBOX, self.OnDraw, self.dropdown)
        self.Bind(wx.EVT_BUTTON, self.OnApply, self.btnapply)
        self.Bind(wx.EVT_BUTTON, self.OnApplyAll, self.btnapplyall)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.btnrem)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveAll, self.btnremyall)



        # Sizers
        topSizer = wx.BoxSizer(wx.VERTICAL)

        text1sizer = wx.BoxSizer(wx.HORIZONTAL)
        text1sizer.Add(self.rbtnfile)
        text1sizer.Add(self.btnbrowse)

        text2sizer = wx.BoxSizer(wx.HORIZONTAL)
        text2sizer.Add(self.rbtnhand)
        text2sizer.Add(self.spinctrl)

        textmeansizer = wx.BoxSizer(wx.HORIZONTAL)
        textmeansizer.Add(textmeanavg)
        textmeansizer.Add(self.textmean)

        dropsizer = wx.BoxSizer(wx.HORIZONTAL)
        dropsizer.Add(textdropdown)
        droprightsizer = wx.BoxSizer(wx.VERTICAL)
        dropsizer.Add(droprightsizer)
        droprightsizer.Add(self.dropdown)
        droprightsizer.Add(self.textafterdropdown)

        applysizer = wx.BoxSizer(wx.HORIZONTAL)
        applysizer.Add(textapply)
        applysizer.Add(self.btnapply)
        applysizer.Add(self.btnapplyall)

        remsizer = wx.BoxSizer(wx.HORIZONTAL)
        remsizer.Add(textrem)
        remsizer.Add(self.btnrem)
        remsizer.Add(self.btnremyall)

        topSizer.Add(textinit)
        topSizer.Add(text1sizer)
        topSizer.Add(text2sizer)
        topSizer.Add(self.textfile)
        topSizer.Add(textmeansizer)
        topSizer.Add(textname)
        topSizer.Add(self.bgname)
        topSizer.Add(self.btnimport)
        topSizer.Add(dropsizer)
        topSizer.Add(applysizer)
        topSizer.Add(remsizer)

        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.Show(True)

        ## Canvas
        self.canvas = plot.PlotCanvas(self.sp)

        # Sizes

        psize = panel.GetBestSize()
        initial_size = (psize[0],psize[1]+200)
        self.SetSize(initial_size)
        sashsize = psize[1]+3
        # This is also necessary to prevent unsplitting
        self.sp.SetMinimumPaneSize(sashsize)
        self.sp.SplitHorizontally(panel, self.canvas, sashsize)


    def OnApply(self, event):
        Page = self.parent.notebook.GetCurrentPage()
        item = self.dropdown.GetSelection()
        Page.bgselected = item - 1
        self.btnrem.Enable(True)
        Page.PlotAll()

    def OnApplyAll(self, event):
        N = self.parent.notebook.GetPageCount()
        item = self.dropdown.GetSelection()
        self.btnrem.Enable(True)
        for i in np.arange(N):
            # Set Page 
            Page = self.parent.notebook.GetPage(i)
            Page.bgselected = item - 1
            try:
                Page.PlotAll()
            except OverflowError:
                errstr = "Could not apply background to Page "+Page.counter+\
                 ". \n Check the value of the trace average and the background."
                dlg = wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg.ShowModal()
                Page.bgselected = None
                

    def OnClose(self, event=None):
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()
            

    def OnBrowse(self, event):
        # opf.BGFiletypes is a dictionary with filetypes that have some
        # trace signal information.
        SupFiletypes = opf.BGFiletypes.keys()
        SupFiletypes.sort()
        filters = ""
        for i in np.arange(len(SupFiletypes)):
            # Add to the filetype filter
            filters = filters+SupFiletypes[i]
            if i != len(SupFiletypes):
                # Add a separator
                filters = filters+"|"
        dlg = wx.FileDialog(self, "Choose a data file", 
            self.parent.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            # Set parent dirname for user comfort
            self.parent.dirname = dirname
            try:
                # [data, trace, curvelist]
                stuff = readfiles.openAnyBG(dirname, filename)
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
                return

            # Usually we will get a bunch of traces. Let the user select which
            # one to take.
            if len(stuff["Filename"]) > 1:
                choices = list()
                for i in np.arange(len(stuff["Filename"])):
                    choices.append(str(i)+". " + stuff["Filename"][i] + " " +
                                   stuff["Type"][i])
                dlg = wx.SingleChoiceDialog(self, "Choose a curve",
                                            "Curve selection", choices=choices)
                if dlg.ShowModal() == wx.ID_OK:
                    selindex = dlg.GetSelection()
                else:
                    return
            else:
                selindex = 0
            
            # If we accidentally recorded a cross correlation curve
            # as the background, let the user choose which trace he wants:
            channelindex = None
            if stuff["Type"][selindex][0:2] == "CC":
                choices = ["Channel 1", "Channel 2"]
                label = "From which channel do you want to use the trace?"
                dlg = wx.SingleChoiceDialog(self, label,
                                "Curve selection", choices=choices)
                if dlg.ShowModal() == wx.ID_OK:
                    channelindex = dlg.GetSelection()
                    trace = stuff["Trace"][selindex][channelindex]
                else:
                    return
            else:
                trace = stuff["Trace"][selindex]

            # Display filename and some of the directory
            self.textfile.SetLabel("File: ..."+dirname[-10:]+"/"+filename)
            name = str(selindex)+". "+stuff["Filename"][selindex]+" "+\
                   stuff["Type"][selindex]
            if channelindex is not None:
                name += " "+str(channelindex+1)
            self.bgname.SetValue(name)
            
            self.trace = trace
            # Calculate average
            self.average = self.trace[:,1].mean()
            # Display average
            self.textmean.SetLabel(str(self.average)+" kHz")
            self.spinctrl.SetValue(self.average)
            # Let the user see the opened file
            self.dropdown.SetSelection(0)
            # show trace
            self.OnDraw()
            # Enable button and editable name
            self.bgname.Enable(True)
            self.btnimport.Enable(True)
        else:
            # User pressed "Abort" - do nothing.
            self.parent.dirname = dlg.GetDirectory()
            dlg.Destroy()
            return

    def OnDraw(self, event=None):
        item = self.dropdown.GetSelection()
        if item <= 0:
            # Disable Apply Buttons
            self.btnapply.Enable(False)
            self.btnapplyall.Enable(False)
            # Draw the trace that was just imported
            if self.trace != None:
                # Calculate average
                self.average = self.trace[:,1].mean()
                self.activetrace = self.trace
                self.textafterdropdown.SetLabel(" Avg:  "+str(self.average)+
                                                " kHz")
                self.textmean.SetLabel(str(self.average))
                self.spinctrl.SetValue(self.average)
            else:
                # Clear the canvas. Looks better.
                self.canvas.Clear()
                # Don't show the average
                self.textafterdropdown.SetLabel("")
                self.textmean.SetLabel("")
                return
        else:
            # Enable Apply Buttons
            self.btnapply.Enable(True)
            self.btnapplyall.Enable(True)
            # Draw a trace from the list
            self.activetrace = self.parent.Background[item-1][2]
            self.textafterdropdown.SetLabel(" Avg:  "+
                                str(self.parent.Background[item-1][0]))
        # We want to have the trace in [s] here.
        trace = 1.*self.activetrace
        trace[:,0] = trace[:,0]/1000
        linesig = plot.PolyLine(trace, legend='', colour='blue', width=1)
        self.canvas.Draw(plot.PlotGraphics([linesig], 
                         xLabel='Measurement time [s]', 
                         yLabel='Background signal [kHz]'))

    def OnImport(self, event):
        self.parent.Background.append([self.average, self.bgname.GetValue(), 
                                      self.trace])
        self.BGlist.append(self.bgname.GetValue())
        self.UpdateDropdown()
        # Let the user see the imported file
        self.dropdown.SetSelection(len(self.BGlist)-1)
        self.btnremyall.Enable(True)
        self.OnDraw()

    def OnPageChanged(self, page):
        # We do not need the *Range* Commands here yet.
        # We open and close the SelectChannelsFrame every time we
        # import some data.
        if page.bgselected is None:
            self.btnrem.Enable(False)
        else:
            self.btnrem.Enable(True)

    def OnRadioFile(self, event):
        # Do not let the user change the spinctrl
        # setting.
        self.spinctrl.Enable(False)
        self.btnbrowse.Enable(True)
        # Restor the old trace
        self.trace = self.oldtrace
        if self.oldfilename is not None:
            self.textfile.SetLabel(self.oldfilename)
        if self.trace is None:
            # Disable button and editable name
            self.bgname.Enable(False)
            self.btnimport.Enable(False)
        # Let us draw
        self.dropdown.SetSelection(0)
        self.OnDraw()

    def OnRadioHand(self, event):
        # Let user enter a signal.
        self.spinctrl.Enable(True)
        self.btnbrowse.Enable(False)
        # save the old trace. We might want to switch back to it.
        if self.trace is not None:
            self.oldtrace = 1.*self.trace
            self.oldfilename = self.textfile.GetLabel()
        self.SpinCtrlChange()
        # Do not show the filename
        self.textfile.SetLabel("No file selected.")
        # Enable button and editable name
        self.bgname.Enable(True)
        self.btnimport.Enable(True)
        if len(self.bgname.GetValue()) == 0:
            # Enter something as name
            self.bgname.SetValue("User")

    def OnRemove(self, event):
        Page = self.parent.notebook.GetCurrentPage()
        Page.bgselected = None
        self.btnrem.Enable(False)
        Page.PlotAll()

    def OnRemoveAll(self, event):
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            Page = self.parent.notebook.GetPage(i)
            Page.bgselected = None
            Page.PlotAll()
    
    def SpinCtrlChange(self, event=None):
        # Let user see the continuous trace we will generate
        self.average = self.spinctrl.GetValue()
        self.trace = np.array([[0,self.average],[1,self.average]])
        self.textmean.SetLabel(str(self.average))
        self.OnDraw()

    def UpdateDropdown(self):
        self.dropdown.SetItems(self.BGlist)

