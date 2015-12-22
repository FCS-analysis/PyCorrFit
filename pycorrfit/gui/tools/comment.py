# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - comment
Edit the sessions' comment.
"""
from __future__ import print_function
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
        self.Bind(wx.EVT_TEXT, self.OnTextChanged, self.control)
        text = wx.StaticText(self.panel, 
                   label="Session comments will be saved in the  session file.")
        # buttons
        btnsave = wx.Button(self.panel, wx.ID_SAVE, 'Save Comment')
        self.Bind(wx.EVT_BUTTON, self.OnSave, btnsave)
        #sizers
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer.Add(text)
        self.topSizer.Add(self.control)
        self.topSizer.Add(btnsave, 1, wx.RIGHT | wx.EXPAND)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        wx.EVT_SIZE(self, self.OnSize)
        self.text_changed = False


    def OnSize(self, event):
        size = event.GetSize()
        sizec = (size[0], size[1]-50)
        self.panel.SetSize(size)
        self.control.SetSize(sizec)


    def OnClose(self, e=None):
        self.parent.filemenu.Check(self.parent.menuComm.GetId(), False)
        if self.text_changed:
            # ask the user to save or discard.
            dlg = wx.MessageDialog(self, "Save comment?",
                                   "Do you want to save the current changes?",
                                   style=wx.YES_NO)
            if dlg.ShowModal() == wx.ID_YES:
                self.OnSave()
        self.Destroy()

    def OnTextChanged(self, e=None):
        """ When the user changes the text
        """
        self.text_changed = True

    def OnSave(self, e=None):
        self.parent.SessionComment = self.control.GetValue()
        self.text_changed = False
        self.OnClose()

