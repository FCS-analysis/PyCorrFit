# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module tools - example
    This is an example tool. You will need to edit __init__.py inside this
    folder to activate it.

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
from scipy import optimize as spopt

import platform






class GlobalFit(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
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

        initial_size = (450,300)
        initial_sizec = (initial_size[0]-6, initial_size[1]-30)
        self.SetMinSize((200,200))
        self.SetSize(initial_size)
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
        # Find maximum page number
        j = 0
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = max(j, int(filter(lambda x: x.isdigit(), Page.counter)))
        if j != 0:
            self.WXTextPages.SetValue("0-"+str(j))
        else:
            self.WXTextPages.SetValue("0")

        self.topSizer.Add(self.WXTextPages)

        ## Button

        btnfit = wx.Button(self.panel, wx.ID_ANY, 'Global fit')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnFit, btnfit)
        self.topSizer.Add(btnfit)

        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.Show(True)

    
    def fit_function(self, parms):
        """
            *parms*: Parameters to fit, array
            needs: 
             self.parmstofit - list (strings) of parameters to fit
                               (corresponding to *parms*)
             self.PageData (dict with dict item = self.PageData["PageNumber"]):
                item["x"]
                item["data"]
                item["modelid"]
                item["values"]
        """
        # The list containing arrays to be minimized
        minimize = list()
        for key in self.PageData.keys():
            # Get the function
            item = self.PageData[key]
            modelid = item["modelid"]
            function = mdls.modeldict[modelid][3]
            values = self.PageData[key]["values"]
            # Set parameters for each function (Page)
            for i in np.arange(len(self.parmstofit)):
                p = self.parmstofit[i]
                labels = mdls.valuedict[modelid][0]
                if p in labels:
                    index = labels.index(p)
                    values[index] = parms[i]
            # Check parameters, if there is such a function
            check_parms = mdls.verification[modelid]
            values = check_parms(values)
            # Write parameters back?
            # self.PageData[key]["values"] = values
            # Calculate resulting correlation function
            # corr = function(item.values, item.x)
            # Subtract data. This is the function we want to minimize
            minimize.append(function(values, item["x"]) - item["data"])

        # Flatten the list and make an array out of it.
        return np.array([item for sublist in minimize for item in sublist])


    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()

    def OnFit(self, e=None):
        # string like this: 1,2,4-9,10
        strFull = self.WXTextPages.GetValue()
        listFull = strFull.split(",")
        PageNumbers = list()
        for item in listFull:
            pagerange = item.split("-")
            start = int(pagerange[0].strip())
            end = int(pagerange[-1].strip())
            for i in np.arange(end-start+1)+start:
                PageNumbers.append(i)
        # Remove duplicates (not necessary)
        # PageNumbers = dict.fromkeys(PageNumbers).keys()
        ## Get the corresponding pages, if they exist:
        self.PageData = dict()
        self.parmstofit = list()
        fitparms = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                dataset = dict()
                try:
                    dataset["x"] = Page.dataexp[:,0]
                    dataset["data"] = Page.dataexp[:,1]
                except:
                    print "No experimental data in page #"+j+"!"
                else:
                    dataset["modelid"] = Page.modelid
                    Page.apply_parameters()
                    dataset["values"] = Page.active_parms[1]
                    self.PageData[j] = dataset

                    # Get the parameters to fit from that page
                    labels = Page.active_parms[0]
                    parms = 1*Page.active_parms[1]
                    tofit = 1*Page.active_parms[2]
                    for i in np.arange(len(labels)):
                        if tofit[i]:
                            if self.parmstofit.count(labels[i]) == 0:
                                self.parmstofit.append(labels[i])
                                fitparms.append(parms[i])
        fitparms = np.array(fitparms)
        # Now we can perform the least squares fit
        if len(fitparms) == 0:
            return
        self.parmoptim, self.mesg = spopt.leastsq(self.fit_function, 
                                                  fitparms[:])
        # So we have the optimal parameters.
        # We would like to give each page a chi**2 and its parameters back:
        for key in self.PageData.keys():
            # Get the Page:
            for i in np.arange(self.parent.notebook.GetPageCount()):
                aPage = self.parent.notebook.GetPage(i)
                j = filter(lambda x: x.isdigit(), aPage.counter)
                if int(j) == int(key):
                    Page = aPage
            # Get the function
            item = self.PageData[key]
            modelid = item["modelid"]
            function = mdls.modeldict[modelid][3]
            values = 1*Page.active_parms[1]
            # Set parameters for each Page)
            for i in np.arange(len(self.parmstofit)):
                p = self.parmstofit[i]
                labels = mdls.valuedict[modelid][0]
                if p in labels:
                    index = labels.index(p)
                    values[index] = self.parmoptim[i]
                    Page.active_parms[2][index] = True
            # Check parameters, if there is such a function
            check_parms = mdls.verification[modelid]
            values = check_parms(values)
            # Write parameters back?
            Page.active_parms[1] = 1*values
            # Calculate resulting correlation function
            # corr = function(item.values, item.x)
            # Subtract data. This is the function we want to minimize
            residual = function(values, item["x"]) - item["data"]
            # Calculate chi**2
            Page.chi2 = np.sum(residual**2)
            Page.apply_parameters_reverse()
            Page.PlotAll()


    def OnPageChanged(self, page):
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        self.Page = page
        pass


