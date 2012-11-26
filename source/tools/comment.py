# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - comment
    Just edit the sessions comment.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""

import wx



class EditComment(wx.Frame):
    """ Little Dialog to edit the comment on the session. """
    def __init__(self, parent):
        ## Variables
        # parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=parent, title="Session comment",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        initial_size = (400,300)
        initial_sizec = (initial_size[0], initial_size[1]-50)
        self.SetSize(initial_size)

        ## Content
        self.panel = wx.Panel(self)

        self.control = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, 
                        size=initial_sizec, value=self.parent.SessionComment)

        text = wx.StaticText(self.panel, 
                   label="Session comments will be saved in the  session file.")
        btnclose = wx.Button(self.panel, wx.ID_ANY, 'Close')
        btnokay = wx.Button(self.panel, wx.ID_ANY, 'OK')
        self.Bind(wx.EVT_BUTTON, self.OnClose, btnclose)
        self.Bind(wx.EVT_BUTTON, self.OnOkay, btnokay)
        
        self.topSizer = wx.BoxSizer(wx.VERTICAL)

        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(btnclose, 1)
        buttonsizer.Add(btnokay, 1)

        self.topSizer.Add(text)
        self.topSizer.Add(buttonsizer)
        self.topSizer.Add(self.control)

        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.Show(True)
        wx.EVT_SIZE(self, self.OnSize)

    def OnSize(self, event):
        size = event.GetSize()
        sizec = (size[0], size[1]-50)
        self.panel.SetSize(size)
        self.control.SetSize(sizec)

    def OnClose(self, event=None):
        self.parent.filemenu.Check(self.parent.menuComm.GetId(), False)
        self.Destroy()

    def OnOkay(self, event):
        self.parent.SessionComment = self.control.GetValue()
        self.OnClose()

