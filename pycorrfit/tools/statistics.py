# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - statistics
Provide the user with tab-separated statistics of their curves.
Values are sorted according to the page number.
"""
from __future__ import division

import codecs
import wx
import wx.lib.plot as plot              # Plotting in wxPython
import wx.lib.scrolledpanel as scrolled
import numpy as np
import re

from .info import InfoClass
from .. import misc
from .. import models as mdls


# Menu entry name
MENUINFO = ["&Statistics view", "Show some session statistics."]

def run_once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


class Stat(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent):
        self.MyName="STATISTICS"
        # parent is the main frame of PyCorrFit
        self.boxsizerlist = list()
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Statistics",
                 pos=pos, size=(700,600),
                 style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        self.MyName = "STATISTICS"
        # List of parameters that are plotted or not
        self.PlotParms = list(["None", 0])
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
        # Pagenumbers
        self.PageNumbers =range(1,1+self.parent.notebook.GetPageCount())
        ## Splitter window. left side: checkboxes
        ##                  right side: plot with parameters
        self.sp = wx.SplitterWindow(self, style=wx.SP_3DSASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.sp.SetMinimumPaneSize(1)
        ## Content
        # We will display a dialog that conains all the settings
        # - Which model we want statistics on
        # - What kind of parameters should be printed
        #   (We will get the parameters from the current page)
        #   If on another page, the parameter is not available,
        #   do not make a mess out of it.
        # Then the user presses a button and sees/saves the table
        # with all the info.
        self.panel = scrolled.ScrolledPanel(self.sp)
        self.panel.SetupScrolling(scroll_y=True)
        # Parameter settings.
        if self.parent.notebook.GetPageCount() != 0:
            self.InfoClass = InfoClass(CurPage=self.Page)
        else:
            self.panel.Disable()
        # A dropdown menu for the source Page:
        text = wx.StaticText(self.panel, 
                    label="Create a table with all the selected\n"+
                          "variables below from pages with the\n"+
                          "same model as the current page.")
        ## Page selection as in average tool
        Pagetext = wx.StaticText(self.panel, 
                             label="Curves ")
        Psize = text.GetSize()[0]/2
        self.WXTextPages = wx.TextCtrl(self.panel, value="",
                                       size=(Psize,-1))
        # Set number of pages
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(),
                                                        Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        ## Plot parameter dropdown box
        self.PlotParms = self.GetListOfPlottableParms()
        Parmlist = self.PlotParms
        DDtext = wx.StaticText(self.panel, label="Plot parameter ")
        self.WXDropdown = wx.ComboBox(self.panel, -1, "", 
                                size=(Psize,-1), choices=Parmlist,
                                style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnDropDown, self.WXDropdown)
        self.Bind(wx.EVT_TEXT, self.OnDropDown, self.WXTextPages)
        self.WXDropdown.SetSelection(0)
        ## Show Average and SD
        textavg = wx.StaticText(self.panel, label="Average ")
        textsd = wx.StaticText(self.panel, label="Standard deviation ")
        self.WXavg = wx.TextCtrl(self.panel, size=(Psize,-1))
        self.WXsd = wx.TextCtrl(self.panel, size=(Psize,-1))
        self.WXavg.SetEditable(False)
        self.WXsd.SetEditable(False)
        # Create space for parameters
        self.box = wx.StaticBox(self.panel, label="Export parameters")
        self.masterboxsizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        self.masterboxsizer.Add(text)
        self.boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.masterboxsizer.Add(self.boxsizer)
        self.Checkboxes = list()
        self.Checklabels = list()
        if self.parent.notebook.GetPageCount() != 0:
            self.OnChooseValues()
        self.btnSave = wx.Button(self.panel, wx.ID_ANY, 'Save')
        self.Bind(wx.EVT_BUTTON, self.OnSaveTable, self.btnSave)
        # Add elements to sizer
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        GridAll = wx.FlexGridSizer(rows=4, cols=2, vgap=5, hgap=5)
        GridAll.Add(Pagetext)
        GridAll.Add(self.WXTextPages)
        GridAll.Add(DDtext)
        GridAll.Add(self.WXDropdown)
        GridAll.Add(textavg)
        GridAll.Add(self.WXavg)
        GridAll.Add(textsd)
        GridAll.Add(self.WXsd)
        #Psizer = wx.BoxSizer(wx.HORIZONTAL)
        #Psizer.Add(Pagetext)
        #Psizer.Add(self.WXTextPages)
        #DDsizer = wx.BoxSizer(wx.HORIZONTAL)
        #DDsizer.Add(DDtext)
        #DDsizer.Add(self.WXDropdown)
        #self.topSizer.Add(Psizer)
        #self.topSizer.Add(DDsizer)
        self.topSizer.Add(GridAll)
        self.topSizer.Add(self.masterboxsizer)
        self.topSizer.Add(self.btnSave)
        # Set size of window
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self.panel)
        px = self.topSizer.GetMinSizeTuple()[0]
        
        ## Plotting panel
        self.canvas = plot.PlotCanvas(self.sp)
        self.canvas.SetEnableZoom(True)
        self.sp.SplitVertically(self.panel, self.canvas, px+5)
        ## Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        self.OnDropDown()


    def GetListOfAllParameters(self, e=None, return_std_checked=False,
                                page=None):
        """ Returns sorted list of parameters.
            If return_std_checked is True, then a second list with
            standart checked parameters is returned.
        """
        if page is None:
            page = self.Page
        self.InfoClass.CurPage = page
        # Now that we know our Page, we may change the available
        # parameter options.
        Infodict = self.InfoClass.GetCurInfo()
        # We want to sort the information and have some prechecked 
        # values in the statistics window afterwards.
        # new iteration
        keys = Infodict.keys()
        parms = list()
        errparms = list()

        for key in keys:
            for item in Infodict[key]:
                if item is not None:
                    if key == "fitting" and item[0].startswith("Err "):
                        errparms.append(item)
                    elif len(item) == 2:
                        parms.append(item)

        # Separate checkbox for fit errors
        if len(errparms) > 0:
            parms.append(("Fit errors", errparms))
        
        Info = Stat.SortParameters(parms)

        # List of default checked parameters:
        checked = np.zeros(len(Info), dtype=np.bool)
        # Fit parameters
        pbool = page.corr.fit_parameters_variable
        model = mdls.modeldict[page.corr.fit_model.id]
        pname = mdls.GetHumanReadableParms(model.id, model.parameters[1])[0]
        checkadd = np.array(pname)[pbool]
        for ii, p in enumerate(Info):
            if p[0] in checkadd:
                checked[ii] = True
        # A list with additional strings that should be default checked
        # if found somewhere in the data.
        checklist = ["cpp", "duration", "bg rate", "avg.", "Model name"]
        for i in range(len(Info)):
            item = Info[i]
            for checkitem in checklist:
                if item[0].count(checkitem):
                    checked[i] = True
        # A list with strings that should not be checked:
        nochecklist = []
        for i in range(len(Info)):
            item = Info[i]
            for checkitem in nochecklist:
                if item[0].count(checkitem):
                    checked[i] = False
        
        
        if return_std_checked:
            return Info, checked
        else:
            return Info

        
    def GetListOfPlottableParms(self, e=None, return_values=False,
                                page=None):
        """ Returns list of parameters that can be plotted.
            (This means that the values are convertible to floats)
            If return_values is True, then a second list with
            the corresponding values is returned.
        """
        if page is None:
            page = self.Page
        if self.parent.notebook.GetPageCount() != 0:
            Info = self.GetListOfAllParameters(page=page)
            parmlist = list()
            parmvals = list()
            for item in Info:
                if item is not None and len(item) == 2:
                    try:
                        val = float(item[1])
                    except:
                        pass
                    else:
                        # save the key so we can find the parm later
                        parmlist.append(item[0])
                        parmvals.append(val)
        else:
            parmlist = ["<No Pages>"]
            parmvals = [0]
        if return_values:
            return parmlist, parmvals
        else:
            return parmlist


    def GetWantedParameters(self):
        """
        Updates self.SaveInfo with all the information that will be
        saved to the table.
        """
        strFull = self.WXTextPages.GetValue()
        PageNumbers = misc.parseString2Pagenum(self, strFull)
        # Get the wanted parameters from the selection.
        checked = list()
        for i in np.arange(len(self.Checkboxes)):
            if self.Checkboxes[i].IsChecked() == True:
                checked.append(self.Checklabels[i])
        # Collect all the relevant pages
        pages = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            if Page.modelid == self.Page.corr.fit_model.id:
                # Only pages with same modelid
                if int(Page.counter.strip("#: ")) in PageNumbers:
                    # Only pages selected in self.WXTextPages
                    pages.append(Page)
        self.InfoClass.Pagelist = pages
        AllInfo = self.InfoClass.GetAllInfo()
        self.SaveInfo = list()
        # Some nasty iteration through the dictionaries.
        # Collect all checked variables.
        pagekeys = AllInfo.keys()
        # If pagenumber is larger than 10,
        # pagekeys.sort will not work, because we have strings
        # Define new compare function
        cmp_func = lambda a,b: cmp(int(a.strip().strip("#")),
                                   int(b.strip().strip("#")))
        pagekeys.sort(cmp=cmp_func)
        #for Info in pagekeys:
        #    pageinfo = list()
        #    for item in AllInfo[Info]:
        #        for subitem in AllInfo[Info][item]:
        #            if len(subitem) == 2:
        #                for label in checked:
        #                    if label == subitem[0]:
        #                        pageinfo.append(subitem)
        #
        # We want to replace the above iteration with an iteration that
        # covers missing values. This means checking for
        #    "label == subitem[0]"
        # and iteration over AllInfo with that consition.
        for ii in pagekeys:
            pageinfo = list()
            for label in checked:
                label_in_there = False
                for item in AllInfo[ii]:
                    for subitem in AllInfo[ii][item]:
                        if subitem is not None and len(subitem) == 2:
                            if label == subitem[0]:
                                label_in_there = True
                                pageinfo.append(subitem)
                            elif label == "Fit errors" and subitem[0].startswith("Err "):
                                label_in_there = True
                                pageinfo.append(subitem)
                if label_in_there == False:
                    # No data available
                    pageinfo.append([label, "NaN"])
            self.SaveInfo.append(pageinfo)


    def OnCheckboxChecked(self, e="restore"):
        """
            Write boolean data of checked checkboxes to Page variable
            *StatisticsCheckboxes*. If e=="restore", then we will 
            attempt to get the info back from the page.
        """
        # What happens if a checkbox has been checked?
        # We write the data to the Page
        # (it will not be saved in the session).
        if e=="restore":
            checklist = self.Page.StatisticsCheckboxes
            if checklist is not None:
                if len(checklist) <= len(self.Checkboxes):
                    for i in np.arange(len(checklist)):
                        self.Checkboxes[i].SetValue(checklist[i])
        else:
            checklist = list()
            for cb in self.Checkboxes:
                checklist.append(cb.GetValue())
                self.Page.StatisticsCheckboxes = checklist


    def OnChooseValues(self, event=None):
        """
            Plot the values for the parameter selected by the user.
        """
        Info, checked = self.GetListOfAllParameters(
                                                return_std_checked=True)
        #headcounter = 0
        #headlen = len(head)
        # We will sort the checkboxes in more than one column if there
        # are more than *maxitemsincolumn*
        maxitemsincolumn = np.float(19)
        Sizernumber = int(np.ceil(len(Info)/maxitemsincolumn))
        self.boxsizerlist = list()
        for i in np.arange(Sizernumber):
            self.boxsizerlist.append(wx.BoxSizer(wx.VERTICAL))
        # Start at -1 so the indexes will start at 0 (see below).
        #itemcount = -1
        for i in range(len(Info)):
            #itemcount += 1
            #headcounter += 1
            checkbox = wx.CheckBox(self.panel, label=Info[i][0])
            #if headcounter <= headlen:
            #    checkbox.SetValue(True)
            # Additionally default checked items
            #for checkitem in checklist:
            #    if item[0].count(checkitem):
            #        checkbox.SetValue(True)
            checkbox.SetValue(checked[i])
            # Add checkbox to column sizers
            sizern = int(np.floor(i/maxitemsincolumn))
            self.boxsizerlist[sizern].Add(checkbox)
            self.Checkboxes.append(checkbox)
            self.Checklabels.append(Info[i][0])
            self.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChecked, checkbox)
        # Add sizers to boxsizer
        for sizer in self.boxsizerlist:
            self.boxsizer.Add(sizer)
        self.OnCheckboxChecked("restore")
        self.AllPlotParms = Info


    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


    def OnDropDown(self, e=None):
        """ Plot the parameter selected in WXDropdown
            Uses info stored in self.PlotParms and self.InfoClass
        """
        if self.parent.notebook.GetPageCount() == 0 or self.Page is None:
            self.canvas.Clear()
            return
        
        # Get valid pages
        strFull = self.WXTextPages.GetValue()
        try:
            PageNumbers = misc.parseString2Pagenum(self, strFull,
                                                          nodialog=True)
        except:
            PageNumbers = self.PageNumbers
        else:
            self.PageNumbers = PageNumbers
        
        # Get plot parameters
        DDselid = self.WXDropdown.GetSelection()
        #[label, key] = self.PlotParms[DDselid]
        label = self.PlotParms[DDselid]
        # Get potential pages
        pages = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            if Page.corr.fit_model.id == self.Page.corr.fit_model.id:
                # Only pages with same modelid
                if int(Page.counter.strip("#: ")) in PageNumbers:
                    # Only pages selected in self.WXTextPages
                    pages.append(Page)
        plotcurve = list()
        for page in pages:
            pllabel, pldata = self.GetListOfPlottableParms(page=page,
                                                     return_values=True)
            # Get the labels and make a plot of the parameters
            if len(pllabel)-1 >= DDselid and pllabel[DDselid] == label:
                x = int(page.counter.strip("#: "))
                y = pldata[DDselid]
                plotcurve.append([x,y])
            else:
                # try to get the label by searching for the first
                # instance
                for k in range(len(pllabel)):
                    if pllabel[k] == label:
                        x = int(page.counter.strip("#: "))
                        y = pldata[k]
                        plotcurve.append([x,y])
        # Prepare plotting
        self.canvas.Clear()
        linesig = plot.PolyMarker(plotcurve, size=1.5, marker='circle')
        plotlist = [linesig]
        # average line
        try:
            avg = np.average(np.array(plotcurve)[:,1])
            maxpage =  int(np.max(np.array(plotcurve)[:,0]) +1)
            minpage =  int(np.min(np.array(plotcurve)[:,0]) -1)
        except:
            minpage = 0
            maxpage = 0
            self.WXavg.SetValue("-")
            self.WXsd.SetValue("-")
        else:
            # Plot data
            plotavg = [[0.5, avg], [maxpage+.5, avg]]
            #lineclear = plot.PolyLine(plotavg, colour="black")
            lineclear = plot.PolyMarker(plotavg, colour="black")
            plotlist.append(lineclear)
            # Update Text control
            self.WXavg.SetValue(str(avg))
            self.WXsd.SetValue(str(np.std(np.array(plotcurve)[:,1])))
        # Draw
        # This causes a memory leak after this function has been 
        # called several times with the same large data set.
        # This goes away if only linesig OR lineclear are plotted.
        #
        #graphics = plot.PlotGraphics(plotlist, 
        #                             xLabel='page number', 
        #                             yLabel=label)
        graphics = plot.PlotGraphics([linesig], 
                                     xLabel='page number', 
                                     yLabel=label)
        
        # Correctly set x-axis
        minticks = 2
        self.canvas.SetXSpec(max(maxpage-minpage, minticks))
        self.canvas.Draw(graphics, xAxis=(minpage,maxpage))

        
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
        # filter unwanted triggers to improve speed
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
        elif trigger in ["tab_init"] and page is not None:
            # Check if we have to replot for a new model
            if self.Page.corr.fit_model.id == page.corr.fit_model.id:
                return
        if (trigger in ["page_add_finalize"] and 
            self.WXTextPages.GetValue() == "1"):
            # We probably imported data with statistics window open
            self.PageNumbers = range(1,
                                  1+self.parent.notebook.GetPageCount())
            setstring = misc.parsePagenum2String(self.PageNumbers)
            self.WXTextPages.SetValue(setstring)
            
        #
        # Prevent this function to be run twice at once:
        #
        oldsize = self.GetSizeTuple()
        if self.WXTextPages.GetValue() == "":
            # Set number of pages
            pagenumlist = list()
            for i in np.arange(self.parent.notebook.GetPageCount()):
                Page = self.parent.notebook.GetPage(i)
                pagenumlist.append(int(filter(lambda x: x.isdigit(),
                                                         Page.counter)))
            valstring=misc.parsePagenum2String(pagenumlist)
            self.WXTextPages.SetValue(valstring)
        DDselection = self.WXDropdown.GetValue()
        self.Page = page
        self.InfoClass = InfoClass(CurPage=self.Page)
        self.PlotParms = self.GetListOfPlottableParms()
        # Make sure the selection stays the same
        DDselid = 0
        for i in range(len(self.PlotParms)):
            if DDselection == self.PlotParms[i]:
                DDselid = i
        Parmlist = self.PlotParms
        self.WXDropdown.SetItems(Parmlist)
        self.WXDropdown.SetSelection(DDselid)
        self.panel.Enable()
        for i in np.arange(len(self.Checkboxes)):
            self.Checkboxes[i].Destroy()
        del self.Checkboxes
            #self.Checklabels[i].Destroy() # those cannot be destroyed.
        for i in np.arange(len(self.boxsizerlist)):
            self.boxsizer.Remove(0)
        self.boxsizer.Layout()
        self.boxsizerlist = list()
        self.Checkboxes = list()
        self.Checklabels = list()
        # Disable if there are no pages left
        if self.parent.notebook.GetPageCount() == 0:
            self.panel.Disable()
            self.canvas.Clear()
            return
        self.OnChooseValues()
        self.boxsizer.Layout()
        self.topSizer.Fit(self)
        (ax, ay) = self.GetSizeTuple()
        (px, py) = self.topSizer.GetMinSizeTuple()
        self.sp.SetSashPosition(px+5)
        self.SetMinSize((px+400, py))
        self.SetSize((np.max([px+400,ax,oldsize[0]]),
                      np.max([py,ay,oldsize[1]])))
        # Replot
        self.OnDropDown()


    def OnSaveTable(self, event=None):
        dirname = self.parent.dirname
        dlg = wx.FileDialog(self.parent, "Choose file to save", dirname,
                "", "Text file (*.txt)|*.txt;*.TXT",
                wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if filename.lower().endswith(".txt") is not True:
                filename = filename+".txt"
            dirname = dlg.GetDirectory()
            openedfile = codecs.open(filename, 'w', encoding="utf-8")
            # Get Parameterlist of all Pages with same model id as
            # Self.Page
            # This creates self.SaveInfo:
            self.GetWantedParameters()
            # Write header
            linestring = u""
            for atuple in self.SaveInfo[0]:
                linestring += u"{}\t".format(atuple[0])
            # remove trailing "\t"
            openedfile.write(u"{}\r\n".format(linestring.strip()))
            # Write data         
            for item in self.SaveInfo:
                linestring = u""
                for btuple in item:
                    linestring += u"{}\t".format(btuple[1])
                openedfile.write(linestring.strip()+u"\r\n")
            openedfile.close()
        else:
            dirname = dlg.GetDirectory()
            dlg.Destroy()
        # Give parent the current dirname
        self.parent.dirname = dirname

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)

    @staticmethod
    def SortParameters(parms):
        u"""
        Sort a list of tuples according to the first item.
        The sorting convention was met in issue #113:
        
        - at the beginning: avg. countrates and particle numbers
        - fast components go before slow components:
          e.g. [τ_trip, τ_diff]
        - model parameters are sorted logically according to their origin:
          e.g. [T1, τ_trip1], or [F1, τ_diff1], or [T2, τ_trip2]
        - if the parameter ends with a number, then we sort it to the
          logical blocks - includes n1, n2, etc.
        - at end: other fitting parameters and mode information

        fitting parameters
        
            intensities
            n
            tautrip1
            T1
            tautrip2
            T2
            tau1
            F1
            tau2
            F2
            tau3
            F3
            alpha
            SP
        
        non-fitting parameter
        
            model name
            chisquare
            weighted fit
            interval
            measurement time
            ...
            model id
        """
        
        startswith_sort = [
                           u"avg. signal",
                           u"n",
                           u"T",
                           u"τ_trip",
                           u"F",
                           u"C",
                           u"D",
                           u"τ",
                           u"τ_diff",
                           u"alpha",
                           u"SP",
                           ]

        otherparms = list()

        # append to this list all parameters that might be in another model.
        for m in mdls.models:
            for p in mdls.GetHumanReadableParms(m.id, m.parameters[1])[0]:
                exists = False
                for sw in startswith_sort+otherparms:
                    if p.startswith(sw):
                        exists = True
                if not exists:
                    otherparms.append(p)
        
        # sort the other parameters by name
        otherparms.sort()
        # special offsets to distinguish "T" and "Type":
        special_off_start = ["Type", "Fit"]
        
        
        def rate_tuple(item):
            x = item[0]
            return rate(x)
        
        def rate(x):
            """
            rate a parameter for sorting.
            lower values are at the beginning of the list.
            """
            x = x.split("[")[0]
            # start at the top
            r = 0
            
            # BLOCK OFFSET
            try:
                intx = int(x[-1])
            except:
                pass
            else:
                # penalty: belongs to block
                r += 3 + intx
            
            # STARTSWITH PENALTY
            for p in startswith_sort:
                if x.startswith(p):
                    r += 1 + 3*(startswith_sort.index(p))
                    break
        
            # Block offset integer
            non_decimal = re.compile(r'[^\d]+')
            pnum = non_decimal.sub("", x)
            if len(pnum) > 0:
                r += int(pnum)
                
            if x.count("3D"):
                r -= 3
            if x.count("2D"):
                r -= 0
        
            # Other Parameters
            for p in otherparms:
                if p.startswith(x):
                    r += (otherparms.index(p)) + 3*len(startswith_sort)

            # Special offsets
            for p in special_off_start:
                if x.startswith(p):
                    r += 300

            if r==0:
                r = 10000

            return r


        def compare(x,y):
            """
            rates x and y.
            returns -1, 0, 1 required for common list sort
            """
            rx = rate_tuple(x)
            ry = rate_tuple(y)
            
            return rx-ry

        return sorted(parms, cmp=compare)