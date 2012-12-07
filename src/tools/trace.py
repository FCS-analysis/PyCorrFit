# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - trace
    Show the trace of a file.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""


import wx
import numpy as np
import wx.lib.plot as plot    


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
            linea = plot.PolyLine(self.tracea, legend='Channel 1', 
                                  colour='blue', width=1)
            lineb = plot.PolyLine(self.traceb, legend='Channel 2', 
                                  colour='red', width=1)
            lines = [linea, lineb]
            self.canvas.SetEnableLegend(True)
        else: 
            self.canvas.Clear()
            return
        # Plot lines
        self.canvas.Draw(plot.PlotGraphics(lines, 
                                           xLabel='Measurement time [s]', 
                                           yLabel='Trace signal [kHz]'))


    def OnPageChanged(self, page):
        # When parent changes
        self.Page = page
        self.OnDraw()

