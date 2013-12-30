# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - trace
    Show the trace of a file.

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
import wx.lib.plot as plot    

# Menu entry name
MENUINFO = ["&Trace view", "Show the trace of an opened file."]

class ShowTrace(wx.Frame):
    def __init__(self, parent):
        # parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Trace view",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        # Page
        self.Page = self.parent.notebook.GetCurrentPage()
        ## Canvas
        self.canvas = plot.PlotCanvas(self)
        self.canvas.SetEnableZoom(True)
        if self.parent.notebook.GetPageCount() == 0:
            # We do not need to disable anything here.  user input.
            pass
        else:
            self.OnDraw()
        initial_size = (350,150)
        self.SetSize(initial_size)
        self.SetMinSize(initial_size)
        ## Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)


    def OnClose(self, event=None):
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


    def OnDraw(self):
        if self.Page.trace is not None:
            self.trace = 1*self.Page.trace
            # We want to have the trace in [s] here.
            self.trace[:,0] = self.trace[:,0]/1000
            line = plot.PolyLine(self.trace, legend='', colour='blue',
                                 width=1)
            lines = [line]
            self.canvas.SetEnableLegend(False)
        elif self.Page.tracecc is not None:
            # This means that we have two (CC) traces to plot
            self.tracea = 1*self.Page.tracecc[0]
            self.tracea[:,0] = self.tracea[:,0]/1000
            self.traceb = 1*self.Page.tracecc[1]
            self.traceb[:,0] = self.traceb[:,0]/1000
            linea = plot.PolyLine(self.tracea, legend='channel 1', 
                                  colour='blue', width=1)
            lineb = plot.PolyLine(self.traceb, legend='channel 2', 
                                  colour='red', width=1)
            lines = [linea, lineb]
            self.canvas.SetEnableLegend(True)
        else: 
            self.canvas.Clear()
            return
        # Plot lines
        self.canvas.Draw(plot.PlotGraphics(lines, 
                                           xLabel='time [s]', 
                                           yLabel='count rate [kHz]'))


    def OnPageChanged(self, page=None):
        self.Page = page
        # When parent changes
        if self.parent.notebook.GetPageCount() == 0:
            # Nothing to do
            try:
                self.canvas.Clear()
            except:
                pass
            return
        self.OnDraw()

