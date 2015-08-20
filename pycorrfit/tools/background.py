# -*- coding: utf-8 -*-
""" 
PyCorrFit

Module tools - background
perform background correction here.
"""


import numpy as np
import os
import sys
import traceback                        # for Error handling
import wx
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx.lib.plot as plot    

from .. import misc
from .. import openfile as opf                  # How to treat an opened file
from .. import readfiles
from ..fcs_data_set import Trace

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
        backgroundinit = (
            "Correct the amplitude for non-correlated background.\n"+
            "The background intensity <B> can be either imported\n"+
            "from a blank measurement or set manually.")
        textinit = wx.StaticText(panel, label=backgroundinit)
        # Radio buttons
        self.rbtnfile = wx.RadioButton(panel, -1, 'Blank measurement: ', 
                                        style = wx.RB_GROUP)
        self.rbtnfile.SetValue(True)
        self.btnbrowse = wx.Button(panel, wx.ID_ANY, 'Browse ...')
        self.rbtnhand = wx.RadioButton (panel, -1, 'Manual, <B> [kHz]: ')
        # Spincontrol
        self.spinctrl = floatspin.FloatSpin(panel, digits=4, min_val=0,
                                            increment=.01)
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
        self.BGlist = ["File/User"] # updated by self.UpdateDropdown()
        textdropdown = wx.StaticText(panel, label="Show background: ")
        self.dropdown = wx.ComboBox(panel, -1, "File/User", (15, -1),
                     wx.DefaultSize, self.BGlist, wx.CB_DROPDOWN|wx.CB_READONLY)
        self.UpdateDropdown()
        # Radio buttons Channel1 and 2
        self.rbtnCh1 = wx.RadioButton (panel, -1, 'Ch1 ', 
                                        style = wx.RB_GROUP)
        self.rbtnCh1.SetValue(True)
        self.rbtnCh2 = wx.RadioButton (panel, -1, 'Ch2')
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
        textyma   = wx.StaticText(panel, label="Shortcut - ")
        self.btnapplyall = wx.Button(panel, wx.ID_ANY, 'Apply to all pages')
        textor2 = wx.StaticText(panel, label=" or ")
        self.btnremyall = wx.Button(panel, wx.ID_ANY, 'Dismiss from all pages')
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
        applysizer.Add(self.rbtnCh1)
        applysizer.Add(self.rbtnCh2)
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


    def Apply(self, Page, backgroundid):
        if self.rbtnCh1.GetValue() == True:
            Page.bgselected = backgroundid
        else:
            Page.bg2selected = backgroundid
        if Page.IsCrossCorrelation is False:
            # Autocorrelation only has one background!
            Page.bg2selected = None


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
                self.Apply(Page, item)
                Page.OnAmplitudeCheck("init")
                Page.PlotAll()
        # Clean up unused backgrounds
        CleanupAutomaticBackground(self.parent)


    def OnApplyAll(self, event):
        self.btnrem.Enable(True)
        self.btnremyall.Enable(True)
        N = self.parent.notebook.GetPageCount()
        item = self.dropdown.GetSelection()
        for i in np.arange(N):
            # Set Page 
            Page = self.parent.notebook.GetPage(i)
            try:
                self.Apply(Page, item)
                Page.OnAmplitudeCheck("init")
                Page.PlotAll()
            except OverflowError:
                errstr = "Could not apply background to Page "+Page.counter+\
                 ". \n Check the value of the trace average and the background."
                dlg = wx.MessageDialog(self, errstr, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg.ShowModal()
                Page.bgselected = None
                Page.bg2selected = None
        # Clean up unused backgrounds
        CleanupAutomaticBackground(self.parent)


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
            self.parent.dirname, "", filters, wx.FD_OPEN)
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
            self.activetrace = self.parent.Background[item-1].trace
        # We want to have the trace in [s] here.
        trace = 1.*self.activetrace
        trace[:,0] = trace[:,0]/1000
        linesig = plot.PolyLine(trace, legend='', colour='blue', width=1)
        self.canvas.Draw(plot.PlotGraphics([linesig], 
                         xLabel='time [s]', 
                         yLabel='background signal [kHz]'))


    def OnImport(self, event):
        self.parent.Background.append(Trace(trace=self.trace, name=self.bgname.GetValue()))
        # Next two lines are taken care of by UpdateDropdown
        #name = "{} ({:.2f} kHz)".format(self.bgname.GetValue(), self.average)
        #self.BGlist.append(name)
        self.UpdateDropdown()
        self.btnremyall.Enable(True)
        self.btnrem.Enable(True)
        self.btnapplyall.Enable(True)
        self.btnapply.Enable(True)
        self.OnDraw()
        # Update BG dropdown of each page
        for i in np.arange(self.parent.notebook.GetPageCount()):
            self.parent.notebook.GetPage(i).OnAmplitudeCheck()


    def OnPageChanged(self, page=None, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        # We do not need the *Range* Commands here yet.
        # We open and close the SelectChannelsFrame every time we
        # import some data.
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
        if len(self.parent.Background) == 0:
            self.BGlist = list()
            self.UpdateDropdown()
            self.dropdown.SetValue("File/User")
        if self.parent.notebook.GetPageCount() == 0:
            self.sp.Disable()
            return
        self.sp.Enable()
        if len(self.BGlist) <= 0:
            self.btnrem.Enable(False)
            self.btnremyall.Enable(False)
            self.btnapply.Enable(False)
            self.btnapplyall.Enable(False)
        else:
            self.btnrem.Enable(True)
            self.btnremyall.Enable(True)
            self.btnapply.Enable(True)
            self.btnapplyall.Enable(True)
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
        #item = self.dropdown.GetSelection()
        # Apply to corresponding pages
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                if self.rbtnCh1.GetValue() == True:
                    Page.bgselected = None
                else:
                    Page.bg2selected = None
                Page.bgselected = None
                Page.OnAmplitudeCheck("init")
                Page.PlotAll()
        # Clean up unused backgrounds
        CleanupAutomaticBackground(self.parent)
        

    def OnRemoveAll(self, event):
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            Page = self.parent.notebook.GetPage(i)
            Page.bgselected = None
            Page.bg2selected = None
            Page.OnAmplitudeCheck("init")
            Page.PlotAll()
        # Clean up unused backgrounds
        CleanupAutomaticBackground(self.parent)

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
    
    
    def SpinCtrlChange(self, event=None):
        # Let user see the continuous trace we will generate
        self.average = self.spinctrl.GetValue()
        self.trace = np.array([[0,self.average],[1,self.average]])
        self.textmean.SetLabel(str(self.average))
        self.OnDraw()


    def UpdateDropdown(self, e=None):
        self.BGlist = list()
        #self.BGlist.append("File/User")
        for item in self.parent.Background:
            self.BGlist.append(item.name)
        self.dropdown.SetItems(self.BGlist)
        # Show the last item
        self.dropdown.SetSelection(len(self.BGlist)-1)


def ApplyAutomaticBackground(page, bg, parent):
    """
        Creates an "automatic" background with countrate in kHz *bg* and
        applies it to the given *page* object. If an automatic
        background with the same countrate exists, uses it.
        
        Input:
        *page*   - page to which the background should be applied
        *bg*     - background that should be applied to that page
                   float or list of 1 or two elements
                   -> if the page is cross-correlation, the second
                      background will be applied as well.
        *parent* - parent containing *Background* list
    """
    bglist = 1*np.atleast_1d(bg)
    # minus 1 to identify non-set background id
    bgid = np.zeros(bglist.shape, dtype=int) - 1
    for b in range(len(bglist)):
        bgname = "AUTO: {:e} kHz \t".format(bglist[b])
        # Check if exists:
        for i in xrange(len(parent.Background)):
            if (parent.Background[i].countrate == bglist[b] and 
                parent.Background[i].name == bgname):
                bgid[b] = i
        if bgid[b] == -1:
            # Add new background
            parent.Background.append(Trace(countrate=bglist[b], name=bgname, duration=1))
            bgid[b] = len(parent.Background) - 1
    
    # Apply background to page
    # Last item is id of background

    page.bgselected = bgid[0]
    
    if len(bgid) == 2:
        page.bg2selected = bgid[1]
    else:
        page.bg2selected = None

    CleanupAutomaticBackground(parent)
    page.OnAmplitudeCheck("init")
    page.PlotAll()


def CleanupAutomaticBackground(parent):
    """
        Goes through the pagelist *parent.notebook.GetPageCount()*
        and checks *parent.Background* for unnused automatic
        backgrounds.
        Removes these and updates the references to all backgrounds
        within the pages.
    """
    # Create a dictionary with keys: indices of old background list -
    # and elements: list of pages having this background
    BGdict = dict()
    for i in range(len(parent.Background)):
        BGdict[i] = list()
    # Append pages to the lists inside the dictionary
    for i in range(parent.notebook.GetPageCount()):
        Page = parent.notebook.GetPage(i)
        if Page.bgselected is not None:
            if not BGdict.has_key(Page.bgselected):
                BGdict[Page.bgselected] = list()
            BGdict[Page.bgselected].append([Page, 1])
        if Page.bg2selected is not None:
            if not BGdict.has_key(Page.bg2selected):
                BGdict[Page.bg2selected] = list()
            BGdict[Page.bg2selected].append([Page, 2])
    
    oldBackground = parent.Background
    parent.Background = list()
    bgcounter = 0
    for key in BGdict.keys():
        if len(BGdict[key]) != 0 or not oldBackground[key].name.endswith("\t"):
            parent.Background.append(oldBackground[key])
            for Page, bgid in BGdict[key]:
                if bgid == 1:
                    Page.bgselected = bgcounter
                else:
                    Page.bg2selected = bgcounter
            bgcounter += 1
    # If the background correction tool is open, update the list
    # of backgrounds.
    # (self.MyName="BACKGROUND")
    toolkeys = parent.ToolsOpen.keys()
    if len(toolkeys) == 0:
        pass
    else:
        for key in toolkeys:
            tool = parent.ToolsOpen[key]
            try:
                if tool.MyName == "BACKGROUND":
                    tool.UpdateDropdown()
                    tool.OnPageChanged()
            except:
                pass
