# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - overlaycurves
Let the user choose which correlation curves to use.
Contains wrappers for file import and tools.
"""

try:
    from matplotlib import cm  # @UnresolvedImport
except:
    mpl_available = False
else:
    mpl_available = True
    
import numpy as np
import platform
import wx
import wx.lib.plot as plot              # Plotting in wxPython

from .. import edclasses
from .. import misc

# Menu entry name
MENUINFO = ["&Overlay curves", "Select experimental curves."]

class Wrapper_OnImport(object):
    """ Wrapper for import function.
        parent: wx.Frame
        curvedict: dictionary with curves
        onselected: external function that is called with two arguments:
                    *kept keys* and *unwanted keys* as lists referring to
                    curvedict.
        selkeys: preselected values for curves in curvedict
    """
    def __init__(self, parent, curvedict, onselected,
                 selkeys=None, labels=None):
        self.onselected = onselected
        self.parent = parent
        self.Selector = UserSelectCurves(parent, curvedict, wrapper=self,
                                         selkeys=selkeys, labels=labels)
        self.Selector.Show()
        self.Selector.MakeModal(True)
        self.Selector.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnClose(self, event=None):
        self.Selector.MakeModal(False)
        self.Selector.Destroy()

        
    def OnResults(self, keyskeep, keysrem):
        """ Here we will close (or disable?) pages that are not wanted
            by the user. It is important that we do not close pages that
            do not contain any experimental data (Page.dataeyp is None),
            because we ignored those pages during import.
        """
        self.OnClose()
        self.onselected(keyskeep,keysrem)
        
 


class Wrapper_Tools(object):
    def __init__(self, parent):
        """
        Wrapper for tools menu. Gets curvedict from parent and starts
        curve selection. See *UserSelectCurves* class.
        """
        # parent is the main frame of PyCorrFit
        self.parent = parent
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        ## Wrapping
        curvedict, labels = self.GetCurvedict()
        self.labels = labels
        self.Selector = UserSelectCurves(parent, curvedict,
                                         wrapper=self, labels=labels)
        # This is necessary for parent to deselect and select the tool
        # in the tools menu.
        self.Bind = self.Selector.Bind
        if self.parent.notebook.GetPageCount() == 0:
            self.Selector.sp.Disable()


    def Disable(self):
        self.Selector.Disable()

    def Enable(self, par=True):
        self.Selector.Enable(par)
    
    def GetCurvedict(self, e=None):
        curvedict = dict()
        labels = dict()
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            Page = self.parent.notebook.GetPage(i)
            key = Page.counter
            if Page.corr.correlation is not None:
                curve = 1*Page.corr.correlation_plot
                curvedict[key] = curve
                labels[key] = Page.tabtitle.GetValue()
        return curvedict, labels

        
    def OnClose(self, event=None):
        # This is a necessary function for PyCorrFit.
        # Do not change it.
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Selector.Destroy()


    def OnPageChanged(self, page=None, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        if trigger in ["parm_batch", "fit_batch", "page_add_batch",
                       "tab_init", "tab_browse"]:
            return
        # When parent changes
        # This is a necessary function for PyCorrFit.
        # This is stuff that should be done when the active page
        # of the notebook changes.
        if self.parent.notebook.GetPageCount() == 0:
            self.Selector.SelectBox.SetItems([])
            self.Selector.sp.Disable()
        else:
            oldlabels = self.Selector.curvelabels
            self.Selector.sp.Enable()
            # Sticky behavior cleaned up in 0.7.8
            curvedict, labels = self.GetCurvedict()
            self.Selector.curvedict = curvedict
            self.Selector.labels = labels
            self.Selector.ProcessDict()
            self.labels = labels
            if oldlabels != self.Selector.curvelabels:
                self.Selector.SelectBox.SetItems(
                                              self.Selector.curvelabels)
            for i in np.arange(len(self.Selector.curvekeys)):
                self.Selector.SelectBox.SetSelection(i)
            self.Selector.OnUpdatePlot(trigger=trigger)


    def OnResults(self, keyskeep, keysrem):
        """ Here we will close (or disable?) pages that are not wanted
            by the user. It is important that we do not close pages that
            do not contain any experimental data (Page.dataeyp is None),
            because we ignored those pages during import.
        """
        if len(keysrem) == 0:
            self.OnClose()
            return
        # warn the user!
        # First make a list of all pages that need to be removed and then
        # delete those pages.
        overtext = "Keep only pages in this list?"
        textlist = ""
        for key in keyskeep:
            textlist += "- "+key+" "+self.labels[key]+"\n"
        dlg = edclasses.MyScrolledDialog(self.parent,
                                          overtext, textlist, "Warning")
        if dlg.ShowModal() == wx.ID_OK:
            N = self.parent.notebook.GetPageCount()
            pagerem = list()
            for i in np.arange(N):
                Page = self.parent.notebook.GetPage(i)
                key = Page.counter
                if keysrem.count(key) == 1:
                    pagerem.append(Page)
            for Page in pagerem:
                j = self.parent.notebook.GetPageIndex(Page)
                self.parent.notebook.DeletePage(j)
            self.OnPageChanged()
        dlg.Destroy()
        


    def OnSelectionChanged(self, keylist, trigger=None):
        if len(keylist) == 0:
            return
        # integer type list with page number
        pagelist = list()
        N = self.parent.notebook.GetPageCount()
        for i in np.arange(N):
            Page = self.parent.notebook.GetPage(i)
            key = Page.counter
            if keylist.count(key) == 1:
                pagelist.append(int(key.strip("#: ")))
        # Get open tools
        toolkeys = self.parent.ToolsOpen.keys()
        if len(toolkeys) == 0:
            return
        # Fill
        string = misc.parsePagenum2String(pagelist)
        for key in toolkeys:
            tool = self.parent.ToolsOpen[key]
            try:
                tool.SetPageNumbers(string)
            except:
                # tool does not have this function and hence does not
                # need numbers.
                pass
        
        
class UserSelectCurves(wx.Frame):
    # This tool is derived from a wx.frame.
    def __init__(self, parent, curvedict, wrapper=None, selkeys=None,
                 labels=None):
        """
        *curvedict* is a dictionary that contains the curves. Keys serve as
        identifiers in the curve selection.
        e.g.
        curvelist["#1:"] = np.array[ np.array[0.0,1], np.array[0.0,.971] ...]
        *parent* is the main frame
        *wrapper* is the object to which the chosen keys are given back. If
           it is not None, it must provide a function *OnResults*, accepting
           a list of keys as an argument.
        *selkeys* items in the list *curvedict* that are preelected.
        *labels* dictionary with same keys as *curvelist* - labels of the
           entries in the list. If none, the keys of *curvedict* will be used.        
        """
        # parent is the main frame of PyCorrFit
        self.parent = parent
        self.wrapper = wrapper
        self.curvedict = curvedict
        self.selkeys = selkeys
        self.labels = labels    # can be None
        self.curvelabels = None # filled by self.ProcessDict()
        if self.selkeys is not None:
            newselkeys = list()
            for item in self.selkeys:
                newselkeys.append(str(item))
            self.selkeys = newselkeys
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Overlay curves",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT,
                 size=(800,500))
        ## Pre-process
        self.ProcessDict()
        ## Content
        self.sp = wx.SplitterWindow(self, size=(500,500), style=wx.SP_NOBORDER)
        self.sp.SetMinimumPaneSize(1)
        # Top panel
        panel_top = wx.Panel(self.sp, size=(500,200))
        self.upperSizer = wx.BoxSizer(wx.VERTICAL)
        if platform.system().lower() == 'darwin':
            ctrl = "Apple"
        else:
            ctrl = "Ctrl"
        text = "By holding down the '"+ctrl+"' key, single curves can be \n" +\
               "selected or deselected. The 'Shift' key can be used \n" +\
               "to select groups."
        self.upperSizer.Add(wx.StaticText(panel_top, label=text))
        # Bottom Panel
        self.bottom_sp = wx.SplitterWindow(self.sp, size=(500,300), style=wx.SP_NOBORDER)
        self.bottom_sp.SetMinimumPaneSize(1)
        sizepanelx = 250
        panel_bottom = wx.Panel(self.bottom_sp, size=(sizepanelx,300))
        self.boxSizer = wx.BoxSizer(wx.VERTICAL)
        # Box selection
        style = wx.LB_EXTENDED
        self.SelectBox = wx.ListBox(panel_bottom, size=(sizepanelx,300),
                                    style=style, choices=self.curvelabels)
        for i in np.arange(len(self.curvekeys)):
            self.SelectBox.SetSelection(i)

        # Deselect keys that are not in self.selkeys
        if self.selkeys is not None:
            for i in np.arange(len(self.curvekeys)):
                if self.selkeys.count(self.curvekeys[i]) == 0:
                    self.SelectBox.Deselect(i)
        self.Bind(wx.EVT_LISTBOX, self.OnUpdatePlot, self.SelectBox)
        self.boxSizer.Add(self.SelectBox, wx.EXPAND)
        minsx = self.boxSizer.GetMinSize()[0]
        # Button REMOVE
        btnrem = wx.Button(panel_bottom, wx.ID_ANY, 'Remove selected')
        self.Bind(wx.EVT_BUTTON, self.OnPushResultsRemove, btnrem)
        btnrem.SetMinSize((minsx, -1))
        self.boxSizer.Add(btnrem)
        # Button KEEP
        btnkep = wx.Button(panel_bottom, wx.ID_ANY, 'Keep selected')
        self.Bind(wx.EVT_BUTTON, self.OnPushResultsKeep, btnkep)
        self.boxSizer.Add(btnkep)
        btnkep.SetMinSize((minsx, -1))
        # Button CANCEL
        btncancel = wx.Button(panel_bottom, wx.ID_ANY, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.OnCancel, btncancel)
        self.boxSizer.Add(btncancel)
        btncancel.SetMinSize((minsx, -1))
        # Finish off sizers
        panel_top.SetSizer(self.upperSizer)
        panel_bottom.SetSizer(self.boxSizer)
        self.upperSizer.Fit(panel_top)
        self.boxSizer.Fit(panel_bottom)
        minsize = np.array(self.boxSizer.GetMinSizeTuple()) +\
                  np.array(self.upperSizer.GetMinSizeTuple()) +\
                  np.array((300,30))
        self.SetMinSize(minsize)
        #self.SetSize(minsize)
        #self.SetMaxSize((9999, self.boxSizer.GetMinSizeTuple()[1]))
        # Canvas
        self.canvas = plot.PlotCanvas(self.bottom_sp)
        self.canvas.setLogScale((True, False))  
        self.canvas.SetEnableZoom(True)
        # Splitter window
        self.bottom_sp.SplitVertically(panel_bottom, self.canvas, sizepanelx)
        sizetoppanel = self.upperSizer.GetMinSizeTuple()[1]
        self.sp.SplitHorizontally(panel_top, self.bottom_sp, sizetoppanel)
        self.OnUpdatePlot()
        # Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)

    
    def GetSelection(self):
        keyssel = list()
        for i in self.SelectBox.GetSelections():
            keyssel.append(self.curvekeys[i])
        keysnosel = list()
        for key in self.curvekeys:
            if keyssel.count(key) == 0:
                keysnosel.append(key)
        return keyssel, keysnosel
    
    
    def ProcessDict(self, e=None):
        # Define the order of keys used.
        # We want to sort the keys, such that #10: is not before #1:
        self.curvekeys = self.curvedict.keys()
        # Sorting key function applied to each key before sorting:
        page_num = lambda counter: int(counter.strip().strip(":").strip("#"))
        try:
            for item in self.curvekeys:
                page_num(item)
        except:
            fstr = lambda x: x
        else:
            fstr = page_num
        self.curvekeys.sort(key = fstr)
        if self.labels is None:
            self.curvelabels = self.curvekeys
        else:
            # Use given labels instead of curvekeys.
            self.curvelabels = list()
            for key in self.curvekeys:
                self.curvelabels.append("#"+str(key).strip(":# ")+" "+self.labels[key])


    def OnCancel(self, e=None):
        """ Close the tool """
        self.wrapper.OnClose()
        

    def OnPushResultsRemove(self, e=None):
        # Get keys from selection
        keysrem, keyskeep = self.GetSelection()
        self.wrapper.OnResults(keyskeep, keysrem)


    def OnPushResultsKeep(self, e=None):
        # Get keys from selection
        keyskeep, keysrem = self.GetSelection()
        self.wrapper.OnResults(keyskeep, keysrem)


    def OnUpdatePlot(self, e=None, trigger=None):
        """ What should happen when the selection in *self.SelectBox*
            is changed?
            
            This function will alsy try to call the function
            *self.parent.OnSelectionChanged* and hand over the list of
            currently selected curves. This is an addon for 0.7.8
            where we will control the page selection in the average
            tool.
            If `trigger` is something that occurs during loading of
            data, then we will not replot everything.
        """
        #if e is not None and e.GetEventType() == 10007:
        #    return

        # Get selected curves
        curves = list()
        legends = list()
        selection = self.SelectBox.GetSelections()
        for i in selection:
            curves.append(self.curvedict[self.curvekeys[i]])
            legends.append(self.curvekeys[i])
        # Set color map
        if mpl_available:
            cmap = cm.get_cmap("gist_rainbow")
        # Clear Plot
        self.canvas.Clear()
        # Draw Plot
        lines = list()
        for i in np.arange(len(curves)):
            if mpl_available:
                color = cmap(1.*i/(len(curves)), bytes=True)
                color = wx.Colour(color[0], color[1], color[2])
            else:
                color = "black"
            line = plot.PolyLine(curves[i], legend=legends[i],
                                 colour=color, width=1)
            lines.append(line)
        self.canvas.SetEnableLegend(True)
        if len(curves) != 0:
            self.canvas.Draw(plot.PlotGraphics(lines, 
                         xLabel=u'lag time τ [ms]', 
                         yLabel=u'G(τ)'))
        ## This is an addon for 0.7.8
        keyskeep = list()
        for i in self.SelectBox.GetSelections():
            keyskeep.append(self.curvekeys[i])
        try:
            self.wrapper.OnSelectionChanged(keyskeep, trigger=trigger)
        except:
            pass
