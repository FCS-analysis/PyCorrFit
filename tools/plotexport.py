# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - plotexport
    Let the user create nice plots of our data.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""

# We may import different things from throughout the program:
import wx
import numpy as np
import models as mdls

import platform
if platform.system() == 'Linux':
    from IPython.Shell import IPythonShellEmbed
    ipshell = IPythonShellEmbed()
   #ipshell()


class Tool(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Example Tool",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)

        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None

        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()

        initial_size = (450,300)
        initial_sizec = (initial_size[0]-6, initial_size[1]-30)
        self.SetMinSize((200,200))
        self.SetSize(initial_size)
         ## Content
        self.panel = wx.Panel(self)
        btnexample = wx.Button(self.panel, wx.ID_ANY, 'Example button')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnClose, btncopy)
        

        self.topSizer = wx.BoxSizer(wx.VERTICAL)

        self.topSizer.Add(btncopy)

        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.Show(True)
        wx.EVT_SIZE(self, self.OnSize)


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

    def OnSize(self, event):
        size = event.GetSize()
        sizec = (size[0]-5, size[1]-30)
        self.panel.SetSize(size)
        self.control.SetSize(sizec)


