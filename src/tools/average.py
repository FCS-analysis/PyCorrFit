# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - average
    Creates an average of curves.

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

import misc
import models as mdls

# Menu entry name
MENUINFO = ["&Average data", "Create an average curve from whole session."]

class Average(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        # Define a unique name that identifies this tool
        # Do not change this value. It is important for the Overlay tool
        # (selectcurves.py, *Wrapper_Tools*).
        self.MyName="AVERAGE"
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Average curves",
            pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
         ## Content
        self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        textinit = wx.StaticText(self.panel,
                    label="Create an average from the following pages:")
        self.topSizer.Add(textinit)
        ## Page selection
        self.WXTextPages = wx.TextCtrl(self.panel, value="",
                                       size=(textinit.GetSize()[0],-1))
        self.topSizer.Add(self.WXTextPages)
        ## Chechbox asking for Mono-Model
        self.WXCheckMono = wx.CheckBox(self.panel,
         label="Only use pages with the same model as the first page.")
        self.WXCheckMono.SetValue(True)
        self.topSizer.Add(self.WXCheckMono)
        ## Model selection Dropdown
        textinit2 = wx.StaticText(self.panel,
                                label="Select a model for the average:")
        self.topSizer.Add(textinit2)
        self.WXDropSelMod = wx.ComboBox(self.panel, -1, "", (15,30),
               wx.DefaultSize, [], wx.CB_DROPDOWN|wx.CB_READONLY)
        self.topSizer.Add(self.WXDropSelMod)
        textinit3 = wx.StaticText(self.panel,
         label="This tool averages only over pages with the same type"+\
               "\n(auto- or cross-correlation). Intensity data are"+\
               "\nappended sequentially.")
        self.topSizer.Add(textinit3)
        # Set all values of Text and Strin
        self.SetValues()
        btnavg = wx.Button(self.panel, wx.ID_CLOSE, 'Create average')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnAverage, btnavg)
        self.topSizer.Add(btnavg)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.SetMinSize(self.topSizer.GetMinSizeTuple())
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        self.OnPageChanged(self.Page)


    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


    def OnPageChanged(self, page):
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        idsel = self.WXDropSelMod.GetSelection()
        self.SetValues()
        # Set back user selection:
        self.WXDropSelMod.SetSelection(idsel)
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        self.panel.Enable()
        self.Page = page


    def OnAverage(self, evt=None):
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
        pages = list()
        UsedPagenumbers = list()
        # Reference page is the first page of the selection!
        #referencePage = self.parent.notebook.GetCurrentPage()
        referencePage = None
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            if Page.counter.strip(" :#") == str(PageNumbers[0]):
                referencePage = Page
                break
		if referencePage is not None:
			# If that did not work, we have to raise an error.
			raise IndexError("PyCorrFit could not find the first"+
							 " page for averaging.")
			return
        
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                # Get all pages with the same model?
                if self.WXCheckMono.GetValue() == True:
                    if (Page.modelid == referencePage.modelid and
                       Page.IsCrossCorrelation == referencePage.IsCrossCorrelation):
                        ## Check if the page has experimental data:
                        # If there is an empty page somewhere, don't bother
                        if Page.dataexpfull is not None:
                            pages.append(Page)
                            UsedPagenumbers.append(int(j))
                else:
                    if Page.IsCrossCorrelation == referencePage.IsCrossCorrelation:
                        # If there is an empty page somewhere, don't bother
                        if Page.dataexpfull is not None:
                            pages.append(Page)
                            UsedPagenumbers.append(int(j))
        # If there are no pages in the list, exit gracefully
        if len(pages) <= 0:
            texterr_a = "At least one page with experimental data is\n"+\
                        "required for averaging. Please check the pages\n"+\
                        "that you selected for averaging."
            if self.WXCheckMono.GetValue() == True:
                texterr_a += " Note: You selected\n"+\
                 "to only use pages with same model as the first page."
            wx.MessageDialog(self, texterr_a, "Error", 
                              style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
            return
        # Now get all the experimental data
        explist = list()
        # Two components in case of Cross correlation
        tracetime = [np.array([]), np.array([])]
        tracerate = [np.array([]), np.array([])]
        TraceNumber = 0
        TraceAvailable = False # turns True, if pages contain traces
        for page in pages:
            # experimental correlation curve
            # (at least 1d, because it might be None)
            explist.append(np.atleast_1d(1*page.dataexpfull))
            # trace
            # We will put together a trace from all possible traces
            # Stitch together all the traces.
            if page.IsCrossCorrelation is False:
                trace = [page.trace]
                # trace has one element
                TraceNumber = 1
            else:
                trace = page.tracecc
                # trace has two elements
                TraceNumber = 2
            if trace is not None and trace[0] is not None:
                TraceAvailable = True
                # Works with one or two traces. j = 0 or 1.
                for j in np.arange(TraceNumber):
                    if len(tracetime[j]) != 0:
                        # append to the trace
                        oldend = tracetime[j][-1]
                        newtracetime = 1.*trace[j][:,0]
                        newtracetime = newtracetime + oldend
                        tracetime[j] = np.append(tracetime[j], newtracetime)
                        del newtracetime
                        tracerate[j] = np.append(tracerate[j], trace[j][:,1])
                    else:
                        # Initiate the trace
                        tracetime[j] = 1.*trace[j][:,0]
                        tracerate[j] = 1.*trace[j][:,1]
        # Now check if the length of the correlation arrays are the same:
        len0 = len(explist[0])
        for item in explist[1:]:
            if len(item) != len0:
                # print an error  message
                wx.MessageDialog(self,
                "Averaging over curves with different lengths is not"+\
                "\nsupported. When measuring, please make sure that"+\
                "\nthe measurement time for all curves is the same.",
                "Error", style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                return
        # Now shorten the trace, because we want as little memory usage as
        # possible. I used this algorithm in read_FCS_Confocor3.py as well.
        newtraces = list()
        if TraceAvailable is True:
            for j in np.arange(TraceNumber):
                tracej = np.zeros((len(tracetime[j]),2))
                tracej[:,0] = tracetime[j]
                tracej[:,1] = tracerate[j]
                if len(tracej) >= 500:
                    # We want about 500 bins
                    # We need to sum over intervals of length *teiler*
                    teiler = int(len(tracej)/500)
                    newlength = len(tracej)/teiler
                    newsignal = np.zeros(newlength)
                    # Simultaneously sum over all intervals
                    for k in np.arange(teiler):
                        newsignal = \
                                newsignal+tracej[k:newlength*teiler:teiler][:,1]
                    newsignal = 1.* newsignal / teiler
                    newtimes = tracej[teiler-1:newlength*teiler:teiler][:,0]
                    if len(tracej)%teiler != 0:
                        # We have a rest signal
                        # We average it and add it to the trace
                        rest = tracej[newlength*teiler:][:,1]
                        lrest = len(rest)
                        rest = np.array([sum(rest)/lrest])
                        newsignal = np.concatenate((newsignal, rest), axis=0)
                        timerest = np.array([tracej[-1][0]])
                        newtimes = np.concatenate((newtimes, timerest), axis=0)
                    newtrace=np.zeros((len(newtimes),2))
                    newtrace[:,0] = newtimes
                    newtrace[:,1] = newsignal
                else:
                    # Declare newtrace -
                    # otherwise we have a problem down three lines ;)
                    newtrace = tracej
                newtraces.append(newtrace)
        else:
            newtraces=[None,None]
        # Everything is cleared for averaging
        exparray = np.array(explist)
        averagedata = exparray.sum(axis=0)[:,1]/len(exparray)
        # Create a copy from the first page
        average = 1*exparray[0]
        # Set average data
        average[:,1] = averagedata
        # create new page
        self.IsCrossCorrelation = self.Page.IsCrossCorrelation
        interval = (self.Page.startcrop, self.Page.endcrop)
        # Obtain the model ID from the dropdown selection.
        idsel = self.WXDropSelMod.GetSelection()
        modelid = self.DropdownIndex[idsel]
        self.parent.add_fitting_tab(modelid = modelid)
        self.AvgPage = self.parent.notebook.GetCurrentPage()
        (self.AvgPage.startcrop, self.AvgPage.endcrop) = interval
        self.AvgPage.dataexpfull = average
        self.AvgPage.IsCrossCorrelation = self.IsCrossCorrelation
        if self.IsCrossCorrelation is False:
            newtrace = newtraces[0]
            if newtrace is not None and len(newtrace) != 0:
                self.AvgPage.trace = newtrace
                self.AvgPage.traceavg = newtrace.mean()
            else:
                self.AvgPage.trace = None
                self.AvgPage.traceavg = None
        else:
            if newtraces[0] is not None and len(newtraces[0][0]) != 0:
                self.AvgPage.tracecc = newtraces
            else:
                self.AvgPage.tracecc = None
        self.AvgPage.PlotAll()
        self.AvgPage.Fit_enable_fitting()
        if len(pages) == 1:
            # Use the same title as the first page
            newtabti = referencePage.tabtitle.GetValue()
        else:
            # Create a new tab title
            newtabti = "Average ["+misc.parsePagenum2String(UsedPagenumbers)+"]"
        self.AvgPage.tabtitle.SetValue(newtabti)
        # Set the addition information about the variance from averaging
        Listname = "Average"
        standarddev = exparray.std(axis=0)[:,1]
        if np.sum(np.abs(standarddev)) == 0:
            # The average sd is zero. We probably made an average
            # from only one page. In this case we do not enable
            # average weighted fitting
            pass
        else:
            self.AvgPage.external_std_weights[Listname] = standarddev
            WeightKinds = self.AvgPage.Fitbox[1].GetItems()
            # Attention! Average weights and other external weights should
            # be sorted (for session saving).
            extTypes = self.AvgPage.external_std_weights.keys()
            extTypes.sort() # sorting
            for key in extTypes:
                try:
                    WeightKinds.remove(key)
                except:
                    pass
            LenInternal = len(WeightKinds)
            IndexAverag = extTypes.index(Listname)
            IndexInList = LenInternal + IndexAverag
            for key in extTypes:
                WeightKinds += [key]
            self.AvgPage.Fitbox[1].SetItems(WeightKinds)
            self.AvgPage.Fitbox[1].SetSelection(IndexInList)
        # Keep the average tool open.
        # self.OnClose()

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
        
    def SetValues(self, e=None):
        # Text input
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        # Dropdown
        modelkeys = mdls.modeltypes.keys()
        modelkeys.sort()
        try:
            current_model = self.parent.notebook.GetCurrentPage().modelid
        except:
            current_model = -1
        i = 0
        DropdownList = list()
        self.DropdownIndex = list() # Contains model ids with same index
        current_index = 0
        for modeltype in modelkeys:
            for modelid in mdls.modeltypes[modeltype]:
                DropdownList.append(modeltype+": "+mdls.modeldict[modelid][1])
                self.DropdownIndex.append(str(modelid))
                if str(current_model) == str(modelid):
                    current_index = i
                i+=1
        self.WXDropSelMod.SetItems(DropdownList)
        self.WXDropSelMod.SetSelection(current_index)
