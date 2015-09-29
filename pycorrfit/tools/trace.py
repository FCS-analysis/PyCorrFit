# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - trace
Show the trace of a file.
"""

import numpy as np

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
        initial_size = (780,250)
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
        traces = self.Page.corr.traces
        if len(traces) == 1:
            self.trace = 1*traces[0].trace
            # We want to have the trace in [s] here.
            self.trace[:,0] = self.trace[:,0]/1000
            line = plot.PolyLine(self.trace,
                    legend='{:.2f}kHz'.format(traces[0].countrate),
                    colour='blue', width=1)
            lines = [line]
            self.canvas.SetEnableLegend(False)
            xmax = np.max(self.trace[:,0])
            xmin = np.min(self.trace[:,0])
            ymax = np.max(self.trace[:,1])
            ymin = np.min(self.trace[:,1])
        elif len(traces) == 2:
            # This means that we have two (CC) traces to plot
            self.tracea = 1*traces[0].trace
            self.tracea[:,0] = self.tracea[:,0]/1000
            self.traceb = 1*traces[1].trace
            self.traceb[:,0] = self.traceb[:,0]/1000
            linea = plot.PolyLine(self.tracea,
                    legend='channel 1\n{:.2f}kHz'.format(traces[0].countrate), 
                    colour='blue', width=1)
            lineb = plot.PolyLine(self.traceb, 
                    legend='channel 2\n{:.2f}kHz'.format(traces[1].countrate), 
                    colour='red', width=1)
            lines = [linea, lineb]
            self.canvas.SetEnableLegend(True)
            xmax = max(np.max(self.tracea[:,0]), np.max(self.traceb[:,0]))
            xmin = min(np.min(self.tracea[:,0]), np.min(self.traceb[:,0]))
            ymax = max(np.max(self.tracea[:,1]), np.max(self.traceb[:,1]))
            ymin = min(np.min(self.tracea[:,1]), np.min(self.traceb[:,1]))

        else: 
            self.canvas.Clear()
            return
        # Plot lines
        self.canvas.Draw(plot.PlotGraphics(lines, 
                                           xLabel='time [s]', 
                                           yLabel='count rate [kHz]'),
                                           xAxis=(xmin,xmax),
                                           yAxis=(ymin,ymax))


    def OnPageChanged(self, page=None, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
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

