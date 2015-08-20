# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - average
Creates an average of curves.
"""


import numpy as np
import wx

from .. import misc
from .. import models as mdls

# Menu entry name
MENUINFO = ["&Average data", "Create an average curve from whole session."]

class Average(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        # Define a unique name that identifies this tool
        # Do not change this value. It is important for the Overlay tool
        # (selectcurves.py, *Wrapper_Tools*).
        self.MyName="AVERAGE"
        # parent is the main frame of PyCorrFit
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Average curves",
            pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
        ## Content
        self.panel = wx.Panel(self)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        textinit = wx.StaticText(self.panel,
                    label="Create an average from the following pages:")
        self.topSizer.Add(textinit)
        ## Page selection
        self.WXTextPages = wx.TextCtrl(self.panel, value="",
                                       size=(textinit.GetSize()[0],-1))
        self.topSizer.Add(self.WXTextPages)
        ## Chechbox asking for Mono-Model
        self.WXCheckMono = wx.CheckBox(self.panel,
         label="Only use pages with the same model as the first page.")
        self.WXCheckMono.SetValue(True)
        self.topSizer.Add(self.WXCheckMono)
        ## Model selection Dropdown
        textinit2 = wx.StaticText(self.panel,
                                label="Select a model for the average:")
        self.topSizer.Add(textinit2)
        self.WXDropSelMod = wx.ComboBox(self.panel, -1, "", (15,30),
               wx.DefaultSize, [], wx.CB_DROPDOWN|wx.CB_READONLY)
        self.topSizer.Add(self.WXDropSelMod)
        textinit3 = wx.StaticText(self.panel,
         label="This tool averages only over pages with the same type"+\
               "\n(auto- or cross-correlation). Intensity data are"+\
               "\nappended sequentially.")
        self.topSizer.Add(textinit3)
        # Set all values of Text and Strin
        self.SetValues()
        btnavg = wx.Button(self.panel, wx.ID_CLOSE, 'Create average')
        # Binds the button to the function - close the tool
        self.Bind(wx.EVT_BUTTON, self.OnAverage, btnavg)
        self.topSizer.Add(btnavg)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        self.SetMinSize(self.topSizer.GetMinSizeTuple())
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        self.OnPageChanged(self.Page)


    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


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
        if trigger in ["parm_batch", "fit_batch", "page_add_batch",
                       "parm_finalize", "fit_finalize"]:
            return
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            return
        
        #idsel = self.WXDropSelMod.GetSelection()
        self.SetValues()
        # Set back user selection:
        #self.WXDropSelMod.SetSelection(idsel)

        self.panel.Enable()
        self.Page = page


    def OnAverage(self, evt=None):
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        if PageNumbers is None:
            # Something went wrong and parseString2Pagenum already displayed
            # an error message.
            return
        pages = list()
        UsedPagenumbers = list()
        # Reference page is the first page of the selection!
        #referencePage = self.parent.notebook.GetCurrentPage()
        referencePage = None
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            if Page.counter.strip(" :#") == str(PageNumbers[0]):
                referencePage = Page
                break

        if referencePage is None:
            # If that did not work, we have to raise an error.
            raise IndexError("PyCorrFit could not find the first"+
							 " page for averaging.")
            return
        
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            corr = Page.corr
            model = Page.corr.fit_model
            j = filter(lambda x: x.isdigit(), Page.counter)
            if int(j) in PageNumbers:
                # Get all pages with the same model?
                if self.WXCheckMono.GetValue() == True:
                    if (model.id == referencePage.corr.fit_model.id and
                       corr.is_cc == referencePage.corr.is_cc):
                        ## Check if the page has experimental data:
                        # If there is an empty page somewhere, don't bother
                        if corr.correlation is not None:
                            pages.append(Page)
                            UsedPagenumbers.append(int(j))
                else:
                    if corr.is_cc == referencePage.corr.is_cc:
                        # If there is an empty page somewhere, don't bother
                        if corr.correlation is not None:
                            pages.append(Page)
                            UsedPagenumbers.append(int(j))
        # If there are no pages in the list, exit gracefully
        if len(pages) <= 0:
            texterr_a = "At least one page with experimental data is\n"+\
                        "required for averaging. Please check the pages\n"+\
                        "that you selected for averaging."
            if self.WXCheckMono.GetValue() == True:
                texterr_a += " Note: You selected\n"+\
                 "to only use pages with same model as the first page."
            wx.MessageDialog(self, texterr_a, "Error", 
                              style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
            return
        # Now get all the experimental data
        explist = list()
        # Two components in case of Cross correlation
        tracetime = [np.array([]), np.array([])]
        tracerate = [np.array([]), np.array([])]
        TraceNumber = 0
        TraceAvailable = False # turns True, if pages contain traces
        for page in pages:
            corr = page.corr
            # experimental correlation curve
            # (at least 1d, because it might be None)
            explist.append(np.atleast_1d(1*corr.correlation))
            # trace
            # We will put together a trace from all possible traces
            # Stitch together all the traces.
            trace = corr.traces
            TraceNumber = len(trace)
            if TraceNumber > 0:
                TraceAvailable = True
                # Works with one or two traces. j = 0 or 1.
                for j in np.arange(TraceNumber):
                    if len(tracetime[j]) != 0:
                        # append to the trace
                        oldend = tracetime[j][-1]
                        # we assume that the first two points in a
                        # trace are equidistant and we will use their
                        # difference as an offset
                        offset = trace[j][:,0][1] - 2*trace[j][:,0][0]
                        newtracetime = 1.*trace[j][:,0] + offset
                        newtracetime = newtracetime + oldend
                        tracetime[j] = np.append(tracetime[j], newtracetime)
                        del newtracetime
                        tracerate[j] = np.append(tracerate[j], trace[j][:,1])
                    else:
                        # Initiate the trace
                        tracetime[j] = 1.*trace[j][:,0]
                        tracerate[j] = 1.*trace[j][:,1]
        # Now check if the length of the correlation arrays are the same:
        len0 = len(explist[0])
        for item in explist[1:]:
            if len(item) != len0:
                # print an error  message
                wx.MessageDialog(self,
                "Averaging over curves with different lengths is not"+\
                "\nsupported. When measuring, please make sure that"+\
                "\nthe measurement time for all curves is the same.",
                "Error", style=wx.ICON_ERROR|wx.OK|wx.STAY_ON_TOP)
                return
        # Now shorten the trace, because we want as little memory usage as
        # possible. I used this algorithm in read_FCS_Confocor3.py as well.
        newtraces = list()
        if TraceAvailable:
            for j in np.arange(TraceNumber):
                tracej = np.zeros((len(tracetime[j]),2))
                tracej[:,0] = tracetime[j]
                tracej[:,1] = tracerate[j]
                if len(tracej) >= 500:
                    # We want about 500 bins
                    # We need to sum over intervals of length *teiler*
                    teiler = int(len(tracej)/500)
                    newlength = len(tracej)/teiler
                    newsignal = np.zeros(newlength)
                    # Simultaneously sum over all intervals
                    for k in np.arange(teiler):
                        newsignal = \
                                newsignal+tracej[k:newlength*teiler:teiler][:,1]
                    newsignal = 1.* newsignal / teiler
                    newtimes = tracej[teiler-1:newlength*teiler:teiler][:,0]
                    if len(tracej)%teiler != 0:
                        # We have a rest signal
                        # We average it and add it to the trace
                        rest = tracej[newlength*teiler:][:,1]
                        lrest = len(rest)
                        rest = np.array([sum(rest)/lrest])
                        newsignal = np.concatenate((newsignal, rest), axis=0)
                        timerest = np.array([tracej[-1][0]])
                        newtimes = np.concatenate((newtimes, timerest), axis=0)
                    newtrace=np.zeros((len(newtimes),2))
                    newtrace[:,0] = newtimes
                    newtrace[:,1] = newsignal
                else:
                    # Declare newtrace -
                    # otherwise we have a problem down three lines ;)
                    newtrace = tracej
                newtraces.append(newtrace)
        else:
            newtraces=[None,None]
        # Everything is cleared for averaging
        exparray = np.array(explist)
        averagedata = exparray.sum(axis=0)[:,1]/len(exparray)
        # Create a copy from the first page
        average = 1*exparray[0]
        # Set average data
        average[:,1] = averagedata
        # create new page
        self.IsCrossCorrelation = self.Page.corr.is_cc
        interval = self.Page.corr.fit_ival
        # Obtain the model ID from the dropdown selection.
        idsel = self.WXDropSelMod.GetSelection()
        modelid = self.DropdownIndex[idsel]
        self.AvgPage = self.parent.add_fitting_tab(modelid = modelid,
                                                   select = True)
        self.AvgPage.corr.fit_ival = interval
        self.AvgPage.corr.correlation = average
        if self.IsCrossCorrelation is False:
            self.AvgPage.corr.corr_type = "AC average"
            newtrace = newtraces[0]
            if newtrace is not None and len(newtrace) != 0:
                self.AvgPage.corr.traces = [newtrace]
            else:
                self.AvgPage.corr.traces = []
        else:
            self.AvgPage.corr.corr_type = "CC average"
            if newtraces[0] is not None and len(newtraces[0][0]) != 0:
                self.AvgPage.corr.traces = newtraces
            else:
                self.AvgPage.corr.traces = []
        self.AvgPage.Fit_enable_fitting()
        if len(pages) == 1:
            # Use the same title as the first page
            newtabti = referencePage.tabtitle.GetValue()
        else:
            # Create a new tab title
            newtabti = "Average ["+misc.parsePagenum2String(UsedPagenumbers)+"]"
        self.AvgPage.tabtitle.SetValue(newtabti)
        # Set the addition information about the variance from averaging
        Listname = "Average"
        listname = Listname.lower()
        standarddev = exparray.std(axis=0)[:,1]
        if np.sum(np.abs(standarddev)) == 0:
            # The average sd is zero. We probably made an average
            # from only one page. In this case we do not enable
            # average weighted fitting
            pass
        else:
            # TODO:
            # kind of hackish to repeat this three times:
            #   self.AvgPage.corr.set_weights(Listname,  standarddev)
            self.AvgPage.corr.set_weights(listname,  standarddev)
            WeightKinds = self.AvgPage.Fitbox[1].GetItems()
            # Attention! Average weights and other external weights should
            # be sorted (for session saving).
            extTypes = self.AvgPage.corr._fit_weight_memory.keys()
            # TODO:
            # find acleaner solution
            extTypes.remove("none")
            extTypes.sort() # sorting
            for key in extTypes:
                try:
                    WeightKinds.remove(key)
                except:
                    pass
            LenInternal = len(WeightKinds)
            IndexAverag = extTypes.index(listname)
            IndexInList = LenInternal + IndexAverag
            for key in extTypes:
                WeightKinds += [key]
            self.AvgPage.Fitbox[1].SetItems(WeightKinds)
            self.AvgPage.Fitbox[1].SetSelection(IndexInList)
            self.AvgPage.corr.set_weights(listname,  standarddev)
            self.AvgPage.apply_parameters()
            self.AvgPage.corr.set_weights(listname,  standarddev)
        self.AvgPage.PlotAll()
        # Keep the average tool open.
        # self.OnClose()

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)
        
    def SetValues(self, e=None):
        # Text input
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        # Dropdown
        modelkeys = mdls.modeltypes.keys()
        modelkeys.sort()
        try:
            current_model = self.parent.notebook.GetCurrentPage().corr.fit_model.id
        except:
            current_model = -1
        i = 0
        DropdownList = list()
        self.DropdownIndex = list() # Contains model ids with same index
        current_index = 0
        for modeltype in modelkeys:
            for modelid in mdls.modeltypes[modeltype]:
                DropdownList.append(modeltype+": "+mdls.modeldict[modelid][1])
                self.DropdownIndex.append(str(modelid))
                if str(current_model) == str(modelid):
                    current_index = i
                i+=1
        self.WXDropSelMod.SetItems(DropdownList)
        self.WXDropSelMod.SetSelection(current_index)
