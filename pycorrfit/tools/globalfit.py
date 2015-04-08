# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - globalfit
    Perform global fitting on pages which share parameters.

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
from scipy import optimize as spopt

from .. import misc
from .. import models as mdls

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
        ## Weighted fitting
        # The weighted fit of the current page will be applied to
        # all other pages.
        self.weightedfitdrop = wx.ComboBox(self.panel)
        ## Bins from left and right: We also don't edit that.
        self.topSizer.Add(self.weightedfitdrop)
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
            minimize.append(
              (function(values, item["x"]) - item["data"]) / item["dataweights"]
                           )

        # Flatten the list and make an array out of it.
        return np.array([it for sublist in minimize for it in sublist])


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
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
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
                    # Get weights
                    weighttype = self.weightedfitdrop.GetSelection()
                    Page.Fitbox[1].SetSelection(weighttype)
                    weightname = self.weightedfitdrop.GetValue()
                    setweightname = Page.Fitbox[1].GetValue()
                    if setweightname.count(weightname) == 0:
                        print "Page "+Page.counter+" has no fitting type '"+ \
                              weightname+"'!"
                    Page.Fit_WeightedFitCheck()
                    Fitting = Page.Fit_create_instance(noplots=True)
                    if Fitting.dataweights is None:
                        dataset["dataweights"] = 1.
                    else:
                        dataset["dataweights"] = Fitting.dataweights
                    self.PageData[int(j)] = dataset
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
        res = spopt.leastsq(self.fit_function, fitparms[:], full_output=1)
        (popt, pcov, infodict, errmsg, ier) = res
        #self.parmoptim, self.mesg = spopt.leastsq(self.fit_function, 
        #                                          fitparms[:])
        self.parmoptim = res[0]
        # So we have the optimal parameters.
        # We would like to give each page a chi**2 and its parameters back:
        # Create a clean list of PageNumbers
        # UsedPages = dict.fromkeys(PageNumbers).keys()
        UsedPages = self.PageData.keys()
        UsedPages.sort()
        for key in UsedPages:
            # Get the Page:
            for i in np.arange(self.parent.notebook.GetPageCount()):
                aPage = self.parent.notebook.GetPage(i)
                j = filter(lambda x: x.isdigit(), aPage.counter)
                if int(j) == int(key):
                    Page = aPage
            Page.GlobalParameterShare = UsedPages
            # Get the function
            item = self.PageData[key]
            modelid = item["modelid"]
            #function = mdls.modeldict[modelid][3]
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
            #residual = function(values, item["x"]) - item["data"]
            # Calculate chi**2
            # Set the parameter error estimates for all pages
            minimized = self.fit_function(self.parmoptim)
            degrees_of_freedom = len(minimized) - len(self.parmoptim) - 1
            self.chi = Page.chi2 = np.sum((minimized)**2) / degrees_of_freedom
            try:
                self.covar = pcov * self.chi
            except:
                self.parmoptim_error = None
            else:
                if self.covar is not None:
                    self.parmoptim_error = np.diag(self.covar)
            p_error = self.parmoptim_error
            if p_error is None:
                Page.parmoptim_error = None
            else:
                Page.parmoptim_error = dict()
                for i in np.arange(len(p_error)):
                    Page.parmoptim_error[self.parmstofit[i]] = p_error[i]
            Page.apply_parameters_reverse()
            # Because we are plotting the weights, we need to update
            # the corresponfing info in each page:
            weightid = self.weightedfitdrop.GetSelection()
            if weightid != 0:
                # We have weights.
                # We need the following information for correct plotting.
                Page.weighted_fit_was_performed = True
                Page.weights_used_for_fitting = Fitting.dataweights
                Page.calculate_corr()
                Page.data4weight = 1.*Page.datacorr
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
        if self.Page is not None:
            weightlist = self.Page.Fitbox[1].GetItems()
            # Do not display knot number for spline. May be different for each page.
            # Remove everything after a "(" in the weightlist string.
            # This way, e.g. the list does not show the knotnumber, which
            # we don't use anyhow.
            # We are doing this for all elements, because in the future, other (?)
            # weighting methods might be implemented.
            #for i in np.arange(len(weightlist)):
            #    weightlist[i] = weightlist[i].split("(")[0].strip()
            weightlist[1] = weightlist[1].split("(")[0].strip()
            self.weightedfitdrop.SetItems(weightlist)
            try:
                # if there is no data, this could go wrong
                self.Page.Fit_create_instance(noplots=True)
                FitTypeSelection = self.Page.Fitbox[1].GetSelection()
            except:
                FitTypeSelection = 0
            self.weightedfitdrop.SetSelection(FitTypeSelection)
            ## Knotnumber: we don't want to interfere
            # The user might want to edit the knotnumbers.
            # self.FitKnots = Page.FitKnots   # 5 by default

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
