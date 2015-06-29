# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - comment
Edit the sessions' comment.
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
        self.SetMinSize((400,300))
        ## Content
        self.panel = wx.Panel(self)
        self.control = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, 
                        size=initial_sizec, value=self.parent.SessionComment)
        text = wx.StaticText(self.panel, 
                   label="Session comments will be saved in the  session file.")
        # buttons
        btnclose = wx.Button(self.panel, wx.ID_ANY, 'Close')
        btnokay = wx.Button(self.panel, wx.ID_ANY, 'OK')
        self.Bind(wx.EVT_BUTTON, self.OnClose, btnclose)
        self.Bind(wx.EVT_BUTTON, self.OnOkay, btnokay)
        #sizers
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(btnclose, 1)
        buttonsizer.Add(btnokay, 1)
        self.topSizer.Add(text)
        self.topSizer.Add(buttonsizer)
        self.topSizer.Add(self.control)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
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

