# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - RangeSelector
    Select the range in which the parameter should reside for fitting.
    This is only the frontend.
    

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


import wx
import numpy as np

import edclasses  # edited floatspin
import models as mdls


class RangeSelector(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, Page):
        # parent is the main frame of PyCorrFit
        self.parent = Page.parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Parameter Range",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
        ## Content
        self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)

        self.WXboxsizerlist = list()
        self.WXparmlist = list()
        self.OnPageChanged(self.Page)
        #Icon
        if self.parent.MainIcon is not None:
            wx.Frame.SetIcon(self, self.parent.MainIcon)
        self.Show(True)


    def FillPanel(self):
        """ Fill the panel with parameters from the page
        """
        
        self.parameter_range = np.zeros(self.Page.parameter_range.shape)
        labels, parmleft = mdls.GetHumanReadableParms(self.Page.modelid,
                                                 self.Page.parameter_range[:,0])
        labels, parmright = mdls.GetHumanReadableParms(self.Page.modelid,
                                                 self.Page.parameter_range[:,1])
        self.parameter_range[:,0] = np.array(parmleft)
        self.parameter_range[:,1] = np.array(parmright)
        # create line
        
        # = wx.BoxSizer(wx.VERTICAL)
        self.WXboxsizer = wx.FlexGridSizer(rows=len(labels), cols=4, vgap=5, hgap=5)
        for i in range(len(labels)):
            left = edclasses.FloatSpin(self.panel, digits=7, increment=.1)
            right = edclasses.FloatSpin(self.panel, digits=7, increment=.1)
            left.SetValue(self.parameter_range[i][0])
            right.SetValue(self.parameter_range[i][1])
            left.Bind(wx.EVT_SPINCTRL, self.OnSetParmRange)
            right.Bind(wx.EVT_SPINCTRL, self.OnSetParmRange)
            text = wx.StaticText(self.panel, label=u'< '+labels[i])
            text2 = wx.StaticText(self.panel, label=u' <')
            self.WXboxsizer.Add(left)
            self.WXboxsizer.Add(text)
            self.WXboxsizer.Add(text2)
            self.WXboxsizer.Add(right)
            self.WXparmlist.append([left, [text, text2], right])

        self.topSizer.Add(self.WXboxsizer)
        self.btnapply = wx.Button(self.panel, wx.ID_ANY, 'Apply')
        self.Bind(wx.EVT_BUTTON, self.OnSetParmRange, self.btnapply)
        self.topSizer.Add(self.btnapply)
        

    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.RangeSelector = None
        self.Destroy()


    def OnPageChanged(self, page=None):
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        self.Page = page
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        self.panel.Enable()
        try:
            self.btnapply.Destroy()
        except:
            pass
        for i in np.arange(len(self.WXparmlist)):
            self.WXparmlist[i][0].Destroy() #start
            self.WXparmlist[i][1][0].Destroy() #pname
            self.WXparmlist[i][1][1].Destroy() #pname
            self.WXparmlist[i][2].Destroy() #end
        del self.WXparmlist
        for i in np.arange(len(self.WXboxsizerlist)):
            self.WXboxsizer.Remove(0)
        self.WXboxsizerlist = list()
        self.WXparmlist = list()
        self.FillPanel()
        self.WXboxsizer.Layout()
        self.topSizer.Layout()
        self.SetMinSize(self.topSizer.GetMinSizeTuple())
        self.topSizer.Fit(self)


    def OnSetParmRange(self, e):
        """ Called whenever something is edited in this frame.
            Writes back parameter ranges to the page
        """
        # Read out parameters from all controls
        for i in range(len(self.WXparmlist)):
            self.parameter_range[i][0] = self.WXparmlist[i][0].GetValue()
            self.parameter_range[i][1] = self.WXparmlist[i][2].GetValue()
            if self.parameter_range[i][0] > self.parameter_range[i][1]:
                self.parameter_range[i][1] = 1.01*np.abs(self.parameter_range[i][0])
                self.WXparmlist[i][2].SetValue(self.parameter_range[i][1])
        # Set parameters
        l, parm0 = mdls.GetInternalFromHumanReadableParm(self.Page.modelid,
                                                     self.parameter_range[:,0])
        l, parm1 = mdls.GetInternalFromHumanReadableParm(self.Page.modelid,
                                                     self.parameter_range[:,1])
        self.Page.parameter_range[:,0] = np.array(parm0)
        self.Page.parameter_range[:,1] = np.array(parm1)
        #self.Page.PlotAll()
        

