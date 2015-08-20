# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - datarange
Let the user choose time domains.
"""


import wx
import numpy as np


# Menu entry name
MENUINFO = ["&Data range",
            "Select an interval of lag times to be used for fitting."]

class SelectChannels(wx.Frame):
    def __init__(self, parent):
        # parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Data range selection",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        ## Start drawing
        panel = wx.Panel(self)
        self.panel = panel
        # Page
        self.Page = self.parent.notebook.GetCurrentPage()
        self.Calc_init(self.Page)
        text1 = wx.StaticText(panel, label=u"The lag times τ are stored as an "+
                                           u"array of length ")
        self.textend = wx.StaticText(panel, label="%d." % self.lentau)
        text2 = wx.StaticText(panel,
                              label=u"You may wish to confine this array. "+
                                    u"This can be done here.")
        ##Spincontrols:
        FlexSpinSizer = wx.FlexGridSizer(rows=2, cols=4, vgap=5, hgap=5)
        FlexSpinSizer.Add(wx.StaticText(panel, label="Channels:"))
        self.spinstart = wx.SpinCtrl(panel, -1, initial=self.left, 
                                     min=self.start0, max=self.end0-1)
        FlexSpinSizer.Add(self.spinstart)
        FlexSpinSizer.Add(wx.StaticText(panel, label=" - "))
        self.spinend = wx.SpinCtrl(panel, -1, initial=self.right, 
                                   min=self.start0+1, max=self.end0)
        FlexSpinSizer.Add(self.spinend)
        FlexSpinSizer.Add(wx.StaticText(panel, label="Times [ms]:"))
        self.TextTimesStart = wx.StaticText(panel, label="None")
        FlexSpinSizer.Add(self.TextTimesStart)
        FlexSpinSizer.Add(wx.StaticText(panel, label=" - "))
        self.TextTimesEnd = wx.StaticText(panel, label="None")
        FlexSpinSizer.Add(self.TextTimesEnd)
        # Buttons
        btnapply = wx.Button(panel, wx.ID_ANY, 'Apply')
        btnapplyall = wx.Button(panel, wx.ID_ANY, 'Apply to all pages')
        self.ButtonApply = btnapply
        self.ButtonApplyAll = btnapplyall
        self.Bind(wx.EVT_BUTTON, self.OnApply, btnapply)
        self.Bind(wx.EVT_BUTTON, self.OnApplyAll, btnapplyall)
        self.Bind(wx.EVT_SPINCTRL, self.OnChangeChannels, self.spinend)
        self.Bind(wx.EVT_SPINCTRL, self.OnChangeChannels, self.spinstart)
        # Checkbox
        self.fixcheck = wx.CheckBox(panel, -1,
             label="Fix current channel selection for all pages.")
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckbox, self.fixcheck)
        # Text
        channelsel = "Leave this window open for a fixed selection."
        text3 = wx.StaticText(panel, label=channelsel)
        # Sizer
        topSizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(btnapply, 1)
        buttonsizer.Add(btnapplyall, 1)
        text1sizer = wx.BoxSizer(wx.HORIZONTAL)
        text1sizer.Add(text1)
        text1sizer.Add(self.textend)
        topSizer.Add(text1sizer)
        topSizer.Add(text2)
        topSizer.AddSpacer(5)
        topSizer.Add(FlexSpinSizer)
        topSizer.Add(self.fixcheck)
        topSizer.Add(text3)
        topSizer.AddSpacer(5)
        topSizer.Add(buttonsizer)
        panel.SetSizer(topSizer)
        topSizer.Fit(self)
        self.SetMinSize(topSizer.GetMinSizeTuple())
        # Get times.
        self.OnChangeChannels()
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        # Show window
        self.Show(True)
        self.OnPageChanged(self.Page)


    def Calc_init(self, parent):
        ## Variables
        # Parent should be the fitting panel -
        # The tab, where the fitting is done.
        self.Page = parent
        if self.Page == None:
            # dummy info
            taufull = np.arange(100)
            self.left = self.right = None
            self.panel.Disable()
        else:
            self.left = self.Page.corr.fit_ival[0]     # starting position
            self.right = self.Page.corr.fit_ival[1]      # ending position
            taufull = self.Page.corr.lag_time
        self.lentau = len(taufull)
        self.start0 = 0                     # left border of interval
        # The interval starts at 0!
        self.end0 = self.lentau - 1         # right border of interval 
        if self.left is None or self.left > self.end0:
            # This means, that either left = right = None
            # or the correlation-array is too small
            self.left = self.start0
        if self.right is None:
            # set the maximum possible value
            self.right = self.end0
        else:
            self.right -=1


    def OnApply(self, event=None):
        self.SetValues()
        self.Page.PlotAll()


    def OnApplyAll(self, event=None):
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            # Set Page 
            Page = self.parent.notebook.GetPage(i)
            # Find out maximal length
            self.SetValues(page=Page)
            Page.PlotAll()
        # Page.PlorAll() calls this function. This results in the wrong data
        # being displayed in an open "View Info" Window. We call it again.
        self.parent.OnFNBPageChanged()


    def OnChangeTimes(self, e=None):
        """ Called, whenever data range in seconds is changed. This updates
            the data range in channels in the window.
            This function might be used in later versions of PyCorrFit.
        """
        pass


    def OnChangeChannels(self, e=None):
        """ Called, whenever data range in channels is changed. This updates
            the data range in seconds in the window.
        """
        if self.Page == None:
            return
        N = len(self.Page.corr.lag_time)
        start = self.spinstart.Value
        end = self.spinend.Value
        # If the initial boundaries are outside of the experimental
        # data array of length N, change the start and end variables.
        start = start*(start < N-2)
        end = min(end, N-1)
        t1 = 1.*self.Page.corr.lag_time[start]
        t2 = 1.*self.Page.corr.lag_time[end]
        self.TextTimesStart.SetLabel("%.4e" % t1)
        self.TextTimesEnd.SetLabel("%.4e" % t2)
        self.OnCheckbox()


    def OnCheckbox(self, event=None):
        """ Set the correct value in the spincontrol, if the checkbox
            is not checked.
        """
        state = self.fixcheck.GetValue()
        if state == True:
            self.OnApplyAll()
            self.ButtonApply.Disable()
            self.ButtonApplyAll.Disable()
        else:
            self.ButtonApply.Enable()
            self.ButtonApplyAll.Enable()
        #self.OnPageChanged(self.Page)
            

    def OnClose(self, event=None):
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


    def OnPageChanged(self, page, trigger=None):
        # We do not need the *Range* Commands here yet.
        # We open and close the SelectChannelsFrame every time we
        # import some data.
        #
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
        # Check if we have a fixed channel selection
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
        else:
            self.panel.Enable()
            # There is a page. We may continue.
            state = self.fixcheck.GetValue()
            if state:
                # We do not need to run Calc_init
                self.SetValues(page=page)
                page.PlotAll(event="init")
            else:
                # We will run it
                self.Calc_init(page)
                self.spinstart.SetRange(self.start0, self.end0-1)
                self.spinstart.SetValue(self.left)
                self.spinend.SetRange(self.start0+1, self.end0)
                self.spinend.SetValue(self.right)
                self.textend.SetLabel("%d." % self.lentau)
                self.OnChangeChannels()



    def SetValues(self, page=None):
        if page is None:
            page = self.Page
        # Get interval
        start = self.spinstart.GetValue()
        end = self.spinend.GetValue() + 1 # +1, [sic]
        if start > end:
            # swap the variables, we are not angry at the user
            start, end = end, start
        # Find out maximal length
        maxlen = len(page.corr.lag_time)
        # Use the smaller one of both, so we do not get an
        # index out of bounds error
        page.corr.fit_ival = [ start*(start < maxlen - 1 ),
                               min(end, maxlen)
                             ]