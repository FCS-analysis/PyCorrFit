# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - average
    Creates an average of curves.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


import numpy as np
import wx

import models as mdls
import doc


class Average(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
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
        textinit = wx.StaticText(self.panel, label=doc.average)
        self.topSizer.Add(textinit)
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
        self.Page = page


    def OnAverage(self, evt=None):
        # Check if current page has experimental data:
        if self.Page.dataexpfull == None:
            dlg = wx.MessageDialog(self, "No data in current page.", "Error", 
                style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
            dlg.ShowModal() == wx.ID_OK
            return
        # Get all pages with the same model
        pages = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            if (Page.modelid == self.Page.modelid and 
                Page.IsCrossCorrelation == self.Page.IsCrossCorrelation):
                # If there is an empty page somewhere, don't bother
                if Page.dataexpfull is not None:
                    pages.append(Page)
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
                dlg = wx.MessageDialog(self, doc.averagedifflen, "Error", 
                    style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                dlg.ShowModal() == wx.ID_OK
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
        self.parent.add_fitting_tab(modelid = self.Page.modelid)
        self.AvgPage = self.parent.notebook.GetCurrentPage()
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
        self.AvgPage.tabtitle.SetValue("Average")
        self.OnClose()

