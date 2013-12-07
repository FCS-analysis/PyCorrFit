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


import numpy as np
import os
import sys
import traceback                        # for Error handling
import wx
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx.lib.plot as plot    

import doc
import misc
import openfile as opf                  # How to treat an opened file
import readfiles

# Menu entry name
MENUINFO = ["&Background correction", "Open a file for background correction."]

class BackgroundCorrection(wx.Frame):
    def __init__(self, parent):
        self.MyName="BACKGROUND"
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
        self.rbtnfile.SetValue(True)
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
        sizeTextn = textname.GetSize()[0]
        self.bgname = wx.TextCtrl(panel, value="", size=(sizeTextn,-1))
        self.bgname.Enable(False)
        self.btnimport = wx.Button(panel, wx.ID_ANY, 'Import into session')
        self.btnimport.Enable(False)
        # Dropdown
        textdropdown = wx.StaticText(panel, label="Show background: ")
        self.BGlist = list()
        #self.BGlist.append("File/User")
        for item in self.parent.Background:
            bgname = "{} ({:.2f} kHz)".format(item[1],item[0])
            self.BGlist.append(bgname)
        if len(self.BGlist) == 0:
            ddlist = ["File/User"]
        else:
            ddlist = 1*self.BGlist
        self.dropdown = wx.ComboBox(panel, -1, "File/User", (15, -1),
                     wx.DefaultSize, ddlist, wx.CB_DROPDOWN|wx.CB_READONLY)
        #self.textafterdropdown = wx.StaticText(panel, label="")
        # Apply buttons
        self.btnapply = wx.Button(panel, wx.ID_ANY, 'Apply')
        textor = wx.StaticText(panel, label=" or ")
        self.btnrem = wx.Button(panel, wx.ID_ANY, 'Dismiss')
        textpages   = wx.StaticText(panel, label=" correction for pages: ")
        self.WXTextPages = wx.TextCtrl(panel, value="")
        # Initial value for WXTextPages
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        
        textyma   = wx.StaticText(panel, label="You may also: ")
        self.btnapplyall = wx.Button(panel, wx.ID_ANY, 'Apply to all pages')
        self.btnapply.Enable(False)
        self.btnapplyall.Enable(False)
        textor2 = wx.StaticText(panel, label=" or ")
        self.btnremyall = wx.Button(panel, wx.ID_ANY, 'Dismiss from all pages')
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
        #droprightsizer.Add(self.textafterdropdown)
        applysizer = wx.BoxSizer(wx.HORIZONTAL)
        applysizer.Add(self.btnapply)
        applysizer.Add(textor)
        applysizer.Add(self.btnrem)
        applysizer.Add(textpages)
        applysizer.Add(self.WXTextPages)
        applysizer.Add(self.btnapplyall)
        allsizer = wx.BoxSizer(wx.HORIZONTAL)
        allsizer.Add(textyma)
        allsizer.Add(self.btnapplyall)
        allsizer.Add(textor2)
        allsizer.Add(self.btnremyall)
        
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
        topSizer.Add(allsizer)
        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.SetMinSize(topSizer.GetMinSizeTuple())
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
        # If there is no page, disable ourselves:
        self.OnPageChanged(self.parent.notebook.GetCurrentPage())
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)


    def OnApply(self, event):
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
        # BG number
        item = self.dropdown.GetSelection()
        # Apply to corresponding pages
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                Page.bgselected = item
                Page.OnAmplitudeCheck("init")
                Page.PlotAll()


    def OnApplyAll(self, event):
        self.btnrem.Enable(True)
        self.btnremyall.Enable(True)
        N = self.parent.notebook.GetPageCount()
        item = self.dropdown.GetSelection()
        for i in np.arange(N):
            # Set Page 
            Page = self.parent.notebook.GetPage(i)
            Page.bgselected = item
            try:
                Page.OnAmplitudeCheck("init")
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
            if i+1 != len(SupFiletypes):
                # Add a separator
                filters = filters+"|"
        dlg = wx.FileDialog(self, "Choose a data file", 
            self.parent.dirname, "", filters, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # Workaround since 0.7.5
            (dirname, filename) = os.path.split(dlg.GetPath())
            #filename = dlg.GetFilename()
            #dirname = dlg.GetDirectory()
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
                wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                return
            # Usually we will get a bunch of traces. Let the user select which
            # one to take.
            if len(stuff["Filename"]) > 1:
                choices = list()
                for i2 in np.arange(len(stuff["Filename"])):
                    choices.append(str(i2)+". " + stuff["Filename"][i2] + " " +
                                   stuff["Type"][i2])
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
            if ( len(stuff["Type"][selindex]) >= 2 and 
                 stuff["Type"][selindex][0:2] == "CC"       ):
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
            if trace is None:
                print "WARNING: I did not find any trace data."
                return
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
        if item < 0:
            # Disable Apply Buttons
            self.btnapply.Enable(False)
            self.btnapplyall.Enable(False)
            # Draw the trace that was just imported
            if self.trace != None:
                # Calculate average
                self.average = self.trace[:,1].mean()
                self.activetrace = self.trace
                #self.textafterdropdown.SetLabel(" Avg:  "+str(self.average)+
                #                                " kHz")
                self.textmean.SetLabel(str(self.average))
                self.spinctrl.SetValue(self.average)
            else:
                # Clear the canvas. Looks better.
                self.canvas.Clear()
                # Don't show the average
                #self.textafterdropdown.SetLabel("")
                self.textmean.SetLabel("")
                return
        else:
            # Enable Apply Buttons
            self.btnapply.Enable(True)
            self.btnapplyall.Enable(True)
            # Draw a trace from the list
            self.activetrace = self.parent.Background[item-1][2]
            #self.textafterdropdown.SetLabel(" Avg:  "+
            #                    str(self.parent.Background[item-1][0]))
        # We want to have the trace in [s] here.
        trace = 1.*self.activetrace
        trace[:,0] = trace[:,0]/1000
        linesig = plot.PolyLine(trace, legend='', colour='blue', width=1)
        self.canvas.Draw(plot.PlotGraphics([linesig], 
                         xLabel='time [s]', 
                         yLabel='background signal [kHz]'))


    def OnImport(self, event):
        self.parent.Background.append([self.average, self.bgname.GetValue(), 
                                      self.trace])
        name = "{} ({:.2f} kHz)".format(self.bgname.GetValue(), self.average)
        self.BGlist.append(name)
        self.UpdateDropdown()
        # Let the user see the imported file
        self.dropdown.SetSelection(len(self.BGlist)-1)
        self.btnremyall.Enable(True)
        self.btnrem.Enable(True)
        self.btnapplyall.Enable(True)
        self.btnapply.Enable(True)
        self.OnDraw()
        # Update BG dropdown of each page
        for i in np.arange(self.parent.notebook.GetPageCount()):
            self.parent.notebook.GetPage(i).OnAmplitudeCheck()


    def OnPageChanged(self, page):
        # We do not need the *Range* Commands here yet.
        # We open and close the SelectChannelsFrame every time we
        # import some data.
        if len(self.parent.Background) == 0:
            self.BGlist = list()
            self.UpdateDropdown()
            self.dropdown.SetValue("File/User")
        if self.parent.notebook.GetPageCount() == 0:
            self.sp.Disable()
            return
        self.sp.Enable()
        if (self.WXTextPages.GetValue() == ""
            and self.parent.notebook.GetPageCount() != 0):
            # Initial value for WXTextPages
            pagenumlist = list()
            for i in np.arange(self.parent.notebook.GetPageCount()):
                Page = self.parent.notebook.GetPage(i)
                pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
            valstring=misc.parsePagenum2String(pagenumlist)
            self.WXTextPages.SetValue(valstring)
        


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
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
        # BG number
        item = self.dropdown.GetSelection()
        # Apply to corresponding pages
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                Page.bgselected = None
                Page.OnAmplitudeCheck("init")
                Page.PlotAll()


    def OnRemoveAll(self, event):
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            Page = self.parent.notebook.GetPage(i)
            Page.bgselected = None
            Page.OnAmplitudeCheck("init")
            Page.PlotAll()

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
    
    def SpinCtrlChange(self, event=None):
        # Let user see the continuous trace we will generate
        self.average = self.spinctrl.GetValue()
        self.trace = np.array([[0,self.average],[1,self.average]])
        self.textmean.SetLabel(str(self.average))
        self.OnDraw()


    def UpdateDropdown(self):
        self.dropdown.SetItems(self.BGlist)

