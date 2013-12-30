# -*- coding: utf-8 -*-
""" PyCorrFit

    Module tools - statistics
    Provide the user with tab-separated statistics of their curves.
    Values are sorted according to the page number.

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
import wx.lib.plot as plot              # Plotting in wxPython
import numpy as np

from info import InfoClass
import misc

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
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        self.MyName = "STATISTICS"
        # List of parameters that are plotted or not
        self.PlotParms = list(["None", 0])
        # Page - the currently active page of the notebook.
        self.Page = self.parent.notebook.GetCurrentPage()
        # Pagenumbers
        self.PageNumbers = np.arange(self.parent.notebook.GetPageCount())
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
        self.panel = wx.Panel(self.sp)
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
        Psize = text.GetSize()[0] - Pagetext.GetSize()[0]
        self.WXTextPages = wx.TextCtrl(self.panel, value="",
                                       size=(Psize,-1))
        # Set number of pages
        pagenumlist = list()
        for i in np.arange(self.parent.notebook.GetPageCount()):
            Page = self.parent.notebook.GetPage(i)
            pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
        valstring=misc.parsePagenum2String(pagenumlist)
        self.WXTextPages.SetValue(valstring)
        ## Plot parameter dropdown box
        self.PlotParms = self.GetListOfPlottableParms()
        Parmlist = self.PlotParms
        DDtext = wx.StaticText(self.panel, 
                             label="Plot parameter ")
        DDsize = text.GetSize()[0] - DDtext.GetSize()[0]
        self.WXDropdown = wx.ComboBox(self.panel, -1, "", size=(DDsize,-1),
                        choices=Parmlist, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnDropDown, self.WXDropdown)
        self.Bind(wx.EVT_TEXT, self.OnDropDown, self.WXTextPages)
        self.WXDropdown.SetSelection(0)
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
        #self.topSizer.Add(text)
        Psizer = wx.BoxSizer(wx.HORIZONTAL)
        Psizer.Add(Pagetext)
        Psizer.Add(self.WXTextPages)
        DDsizer = wx.BoxSizer(wx.HORIZONTAL)
        DDsizer.Add(DDtext)
        DDsizer.Add(self.WXDropdown)
        self.topSizer.Add(Psizer)
        self.topSizer.Add(DDsizer)
        self.topSizer.Add(self.masterboxsizer)
        self.topSizer.Add(self.btnSave)
        # Set size of window
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        (px, py) = self.topSizer.GetMinSizeTuple()

        ## Plotting panel
        self.canvas = plot.PlotCanvas(self.sp)
        self.sp.SplitVertically(self.panel, self.canvas, px+5)
        self.SetMinSize((px+400, py))
        ## Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        self.OnDropDown()


    def GetListOfAllParameters(self, e=None, return_std_checked=False):
        """ Returns sorted list of parameters.
            If return_std_checked is True, then a second list with
            standart checked parameters is returned.
        """
        self.InfoClass.CurPage = self.Page
        # Now that we know our Page, we may change the available
        # parameter options.
        Infodict = self.InfoClass.GetCurInfo()
        # We want to sort the information and have some prechecked values
        # in the statistics window afterwards.
        # new iteration
        keys = Infodict.keys()
        body = list()
        tail = list()

        for key in keys:
            # "title" - filename/title first
            if key == "title":
                for item in Infodict[key]:
                    if len(item) == 2:
                        if item[0] == "filename/title":
                            headtitle = [item]
                        else:
                            tail.append(item)
            # "title" - filename/title first
            elif key == "parameters":
                headparm = list()
                bodyparm = list()
                for parm in Infodict[key]:
                    parminlist = False
                    try:
                        for fitp in Infodict["fitting"]:
                            parmname = parm[0]
                            errname = "Err "+parmname
                            if fitp[0] == errname:
                                headparm.append(parm)
                                parminlist = True
                                headparm.append(fitp)
                    except:
                        # Maybe there was not fit...
                        pass
                    if parminlist == False:
                        bodyparm.append(parm)
            elif key == "fitting":
                for fitp in Infodict[key]:
                    # We added the error data before in the parameter section
                    if str(fitp[0])[0:4] != "Err ":
                        tail.append(fitp)
            elif key == "supplement":
                body += Infodict[key]
            # Append all other items
            elif key == "background":
                body += Infodict[key]
            else:
                for item in Infodict[key]:
                    if item is not None and len(item) == 2:
                        tail.append(item)
        # Bring lists together
        head = headtitle + headparm
        body = bodyparm + body
        
        Info = head + body + tail

        # List of default checked parameters:
        checked = np.zeros(len(Info), dtype=np.bool)
        checked[:len(head)] = True
        # A list with additional strings that should be default checked if found
        # somewhere in the data.
        checklist = ["cpp", "duration", "bg rate"]
        for i in range(len(Info)):
            item = Info[i]
            for checkitem in checklist:
                if item[0].count(checkitem):
                    checked[i] = True

        if return_std_checked:
            return Info, checked
        else:
            return Info

        
    def GetListOfPlottableParms(self, e=None, return_values=False):
        """ Returns sorted list of parameters that can be plotted.
            (This means that the values are convertable to floats)
            If return_values is True, then a second list with
            the corresponding values is returned.
        """
        if self.parent.notebook.GetPageCount() != 0:
            #Info = self.InfoClass.GetPageInfo(self.Page)
            Info = self.GetListOfAllParameters()
            #keys = Info.keys()
            #keys.sort()
            parmlist = list()
            parmvals = list()
            for item in Info:
                if item is not None and len(item) == 2:
                    try:
                        val = float(item[1])
                    except:
                        pass
                    else:
                        # save the key so we can find the parameter later
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
            if Page.modelid == self.Page.modelid:
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
        # covers missing values. This means checking for "label == subitem[0]"
        # and iteration over AllInfo with that consition.
        for Info in pagekeys:
            pageinfo = list()
            for label in checked:
                label_in_there = False
                for item in AllInfo[Info]:
                    for subitem in AllInfo[Info][item]:
                        if subitem is not None and len(subitem) == 2:
                            if label == subitem[0]:
                                label_in_there = True
                                pageinfo.append(subitem)
                if label_in_there == False:
                    # No data available
                    pageinfo.append([label, "NaN"])
            self.SaveInfo.append(pageinfo)


    def OnCheckboxChecked(self, e="restore"):
        """
            Write boolean data of checked checkboxes to Page variable
            *StatisticsCheckboxes*. If e=="restore", then we will attempt
            to get the info back from the page.
        """
        # What happens if a checkbox has been checked?
        # We write the data to the Page (it will not be saved in the session).
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
        Info, checked = self.GetListOfAllParameters(return_std_checked=True)
        #headcounter = 0
        #headlen = len(head)
        # We will sort the checkboxes in more than one column if there
        # are more than *maxitemsincolumn*
        maxitemsincolumn = np.float(25)
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
            PageNumbers = misc.parseString2Pagenum(self, strFull, nodialog=True)
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
            if Page.modelid == self.Page.modelid:
                # Only pages with same modelid
                if int(Page.counter.strip("#: ")) in PageNumbers:
                    # Only pages selected in self.WXTextPages
                    pages.append(Page)
        plotcurve = list()
        for page in pages:
            self.Page = page
            pllabel, pldata = self.GetListOfPlottableParms(return_values=True)
            # Get the labels and make a plot of the parameters
            if len(pllabel)-1 >= DDselid and pllabel[DDselid] == label:
                x = int(page.counter.strip("#: "))
                y = pldata[DDselid]
                plotcurve.append([x,y])
            else:
                # try to get the label by searching for the first instance
                for k in range(len(pllabel)):
                    if pllabel[k] == label:
                        x = int(page.counter.strip("#: "))
                        y = pldata[k]
                        plotcurve.append([x,y])
        # Prepare plotting
        self.canvas.Clear()
        linesig = plot.PolyMarker(plotcurve, size=1.5, fillstyle=wx.TRANSPARENT,
                                  marker='circle')
        plotlist = [linesig]
        # average line

        try:
            avg = np.average(np.array(plotcurve)[:,1])
            maxpage =  np.max(np.array(plotcurve)[:,0])
        except:
            maxpage = 0
        else:
            plotavg = [[0, avg], [maxpage, avg]]
            lineclear = plot.PolyLine(plotavg, colour="black",
            style= wx.SHORT_DASH)
            plotlist.append(lineclear)
        # Draw
        self.canvas.Draw(plot.PlotGraphics(plotlist, 
                             xLabel='page number', 
                             yLabel=label))
        
        # Correctly set x-axis
        minticks = 2
        self.canvas.SetXSpec(max(maxpage, minticks))
        # Zoom out such that we can see the end of all curves
        try:
            xcenter = np.average(np.array(plotcurve)[:,0])
            ycenter = np.average(np.array(plotcurve)[:,1])
            scale = 1.1
            self.canvas.Zoom((xcenter,ycenter), (scale, scale))
        except:
            pass
        # Redraw result
        self.canvas.Redraw()
                         
        
    def OnPageChanged(self, page):
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        #
        # Prevent this function to be run twice at once:
        #
        oldsize = self.GetSizeTuple()
        if self.WXTextPages.GetValue() == "":
            # Set number of pages
            pagenumlist = list()
            for i in np.arange(self.parent.notebook.GetPageCount()):
                Page = self.parent.notebook.GetPage(i)
                pagenumlist.append(int(filter(lambda x: x.isdigit(), Page.counter)))
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
        self.SetSize((np.max([px+400,ax,oldsize[0]]), np.max([py,ay,oldsize[1]])))
        self.SetMinSize((px+400, py))
        # Replot
        self.OnDropDown()


    def OnSaveTable(self, event=None):
        dirname = self.parent.dirname
        dlg = wx.FileDialog(self.parent, "Choose file to save", dirname, "", 
              "Text file (*.txt)|*.txt;*.TXT",
               wx.SAVE|wx.FD_OVERWRITE_PROMPT)
        # user cannot do anything until he clicks "OK"
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if filename.lower().endswith(".txt") is not True:
                filename = filename+".txt"
            dirname = dlg.GetDirectory()
            openedfile = open(filename, 'wb')
            # Get Parameterlist of all Pages with same model id as
            # Self.Page
            # This creates self.SaveInfo:
            self.GetWantedParameters()
            # Write header
            linestring = ""
            for atuple in self.SaveInfo[0]:
                linestring += str(atuple[0])+"\t"
            # remove trailing "\t"
            openedfile.write(linestring.strip()+"\r\n")
            # Write data         
            for item in self.SaveInfo:
                linestring = ""
                for btuple in item:
                    linestring += str(btuple[1])+"\t"
                openedfile.write(linestring.strip()+"\r\n")
            openedfile.close()
        else:
            dirname = dlg.GetDirectory()
            dlg.Destroy()
        # Give parent the current dirname
        self.parent.dirname = dirname

    def SetPageNumbers(self, pagestring):
        self.WXTextPages.SetValue(pagestring)

