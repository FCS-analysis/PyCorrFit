# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - globalfit
Perform global fitting on pages which share parameters.
"""


import wx
import numpy as np

from .. import misc
from ..fcs_data_set import Fit

# Menu entry name
MENUINFO = ["&Global fitting",
            "Interconnect parameters from different measurements."]

class GlobalFit(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        # Define a unique name that identifies this tool
        # Do not change this value. It is important for the Overlay tool
        # (selectcurves.py, *Wrapper_Tools*).
        self.MyName="GLOBALFIT"
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Gobal fitting",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
        ## Content
        self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        textinit = """Fitting of multiple data sets with different models.
Parameter names have to match. Select pages (e.g. 1,3-5,7),
check parameters on each page and start 'Global fit'. 
"""
        self.topSizer.Add(wx.StaticText(self.panel, label=textinit))
        ## Page selection
        self.WXTextPages = wx.TextCtrl(self.panel, value="", size=(330,-1))
        # Set initial value in text control
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        self.topSizer.Add(self.WXTextPages)
        ## Button
        btnfit = wx.Button(self.panel, wx.ID_ANY, 'Global fit')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnFit, btnfit)
        self.topSizer.Add(btnfit)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.SetMinSize(self.topSizer.GetMinSizeTuple())
        self.OnPageChanged(self.Page)
        # Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)

    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()

    def OnFit(self, e=None):
        # process a string like this: "1,2,4-9,10"
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        global_pages = list()
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
        ## Get the correlations
        corrs = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            corr = Page.corr
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                if corr.correlation is not None:
                    Page.apply_parameters()
                    corrs.append(corr)
                    global_pages.append(int(j))
                else:
                    print "No experimental data in page #"+j+"!"

        if len(corrs) == 0:
            return
        
        # Perform fit
        fitter = Fit(corrs, global_fit=True)
        fit_parm_names = [f.split()[0] for f in fitter.fit_parm_names]

        # update fit results
        for corr in corrs:
            corr.fit_results["global parms"] = u", ".join(fit_parm_names)
            corr.fit_results["global pages"] = u", ".join([str(g) for g in global_pages])
        
        # Plot resutls
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in global_pages:
                Page.apply_parameters_reverse()
                Page.PlotAll()

    def OnPageChanged(self, page, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        self.panel.Enable()
        self.Page = page


    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
