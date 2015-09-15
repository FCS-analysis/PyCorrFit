# -*- coding: utf-8 -*-
"""
PyCorrFit

Module tools - info
Open a text window with lots of information.
"""


import wx
import numpy as np

from .. import fcs_data_set
from .. import models as mdls

# Menu entry name
MENUINFO = ["Page &info",
            "Display some information on the current page."]
            
class InfoClass(object):
    """ This class get's all the Info possible from a Page and
        makes it available through a dictionary with headings as keys.
    """
    def __init__(self, CurPage=None, Pagelist=None ):
        # A list of all Pages currently available:
        self.Pagelist = Pagelist
        # The current page we are looking at:
        self.CurPage = CurPage


    def GetAllInfo(self):
        """ Get a dictionary with page titles and an InfoDict as value.
        """
        MultiInfo = dict()
        for Page in self.Pagelist:
            # Page counter includes a whitespace and a ":" which we do not want.
            MultiInfo[Page.counter[:-2]] = self.GetPageInfo(Page)
        return MultiInfo


    def GetCurInfo(self):
        """ Get all the information about the current Page.
            Added for convenience. You may use GetPageInfo.
        """
        return self.GetPageInfo(self.CurPage)


    def GetCurFancyInfo(self):
        """ For convenience. """
        return self.GetFancyInfo(self.CurPage)


    def GetFancyInfo(self, Page):
        """ Get a nice string representation of the Info """
        InfoDict = self.GetPageInfo(Page)
        # Version
        Version = u"PyCorrFit v."+InfoDict["version"][0]+"\n"
        # Title
        Title = u"\n"
        for item in InfoDict["title"]:
            Title = Title + item[0]+"\t"+ item[1]+"\n"
        # Parameters
        Parameters = u"\nParameters:\n"
        for item in InfoDict["parameters"]:
            Parameters = Parameters + u"  "+item[0]+"\t"+ str(item[1])+"\n"
        # Supplementary parameters
        Supplement = u"\nSupplementary parameters:\n"
        try:
            for item in InfoDict["supplement"]:
                Supplement = Supplement + "  "+item[0]+"\t"+ str(item[1])+"\n"
        except KeyError:
            Supplement = ""
        # Fitting
        Fitting = u"\nFitting:\n"
        try:
            for item in InfoDict["fitting"]:
                Fitting = Fitting + "  "+item[0]+"\t"+unicode(item[1])+"\n"
        except KeyError:
            Fitting = ""
        # Background
        Background = u"\nBackground:\n"
        try:
            for item in InfoDict["background"]:
                Background = Background + "  "+item[0]+"\t"+str(item[1])+"\n"
        except KeyError:
            Background = ""

        # Function doc string
        ModelDoc = u"\n\nModel doc string:\n       " + InfoDict["modeldoc"][0]
        # Supplementary variables
        try:
            SupDoc = u"\n"+8*" "+InfoDict["modelsupdoc"][0]
        except:
            SupDoc = u""
        PageInfo = Version+Title+Parameters+Supplement+Fitting+Background+\
                   ModelDoc+SupDoc
        return PageInfo


    def GetPageInfo(self, Page):
        """ Needs a Page and gets all information from it """
        Page.PlotAll("init")
        # A dictionary with headings as keys and lists of singletts/tuples as 
        # values. If it is a tuple, it might me interesting for a table.
        InfoDict = dict()
        # Get Correlation
        corr = Page.corr
        
        # Get model information
        model = corr.fit_model
        parms = corr.fit_parameters
        fct = corr.fit_model.function.__name__
        InfoDict["version"] = [Page.parent.version]
        Title = list()
        # The tool statistics relys on the string "filename/title".
        # Do not change it!
        if len(model[1]) == 0:
            # Prevent saving no title
            model[1] = "NoName"
        Title.append(["filename/title", Page.title])
        Title.append(["Model species", model.components])
        Title.append(["Model name", model.name])
        Title.append(["Model ID", str(model.id)]) 
        Title.append(["Model function", fct]) 
        Title.append(["Page number", Page.counter[1:-2]]) 
        ## Parameters
        Parameters = list()
        # Use this function to determine human readable parameters, if possible
        Units, Newparameters = mdls.GetHumanReadableParms(model.id, parms)
        # Add Parameters
        for i in np.arange(len(parms)):
            Parameters.append([ Units[i], Newparameters[i] ])
        InfoDict["parameters"] = Parameters
        # Add some more information if available
        # Info is a dictionary or None
        MoreInfo = mdls.GetMoreInfo(model.id, Page)
        if MoreInfo is not None:
            InfoDict["supplement"] = MoreInfo
            # Try to get the dictionary entry of a model
            try:
                # This function should return all important information
                # that can be calculated from the given parameters.
                func_info = mdls.supplement[model.id]
            except KeyError:
                # No information available
                pass
            else:
                InfoDict["modelsupdoc"] = [func_info.func_doc]
        ## Fitting
        
        
        if hasattr(corr, "fit_results"):
            Fitting = list()
            weightedfit = corr.fit_results["weighted fit"]
            if corr.correlation is not None:
                # Mode AC vs CC
                if corr.is_cc:
                    Title.append(["Type AC/CC", "Cross-correlation" ]) 
                else:
                    Title.append(["Type AC/CC", "Autocorrelation" ]) 
                Fitting.append([ u"χ²", corr.fit_results["chi2"]])
                if weightedfit:
                    try:
                        Fitting.append(["Weighted fit", corr.fit_results["weighted fit type"]])
                    except KeyError:
                        Fitting.append(["Weighted fit", u""+Page.Fitbox[1].GetValue()])
                if corr.fit_results.has_key("chi2 type"):
                    ChiSqType = corr.fit_results["chi2 type"]
                else:
                    ChiSqType = "unknown"
                Fitting.append([ u"χ²-type", ChiSqType])
                Fitting.append([ "Algorithm", fcs_data_set.Algorithms[corr.fit_algorithm][1]])
                if len(Page.GlobalParameterShare) != 0:
                    shared = str(Page.GlobalParameterShare[0])
                    for item in Page.GlobalParameterShare[1:]:
                        shared += ", "+str(item)
                    Fitting.append(["Shared parameters with Pages", shared])
                if corr.fit_results.has_key("weighted fit bins"):
                    Fitting.append(["Std. channels", 2*corr.fit_results["weighted fit bins"]+1])
                # Fitting range:
                t1 = 1.*corr.lag_time[corr.fit_ival[0]]
                t2 = 1.*corr.lag_time[corr.fit_ival[1]-1]
                Fitting.append([ "Ival start [ms]", "%.4e" % t1 ])
                Fitting.append([ "Ival end [ms]", "%.4e" % t2 ])
                # Fittet parameters
                try:
                    fitparmsid = corr.fit_results["fit parameters"]
                except:
                    fitparmsid = corr.fit_parameters_variable
                fitparms = np.array(corr.fit_model.parameters[0])[fitparmsid]
                fitparms_short = [ f.split()[0] for f in fitparms ]
                fitparms_short = u", ".join(fitparms_short)
                Fitting.append(["Fit parm.", fitparms_short])
                # global fitting
                for key in corr.fit_results.keys():
                    if key.startswith("global"):
                        Fitting.append([key.capitalize(), corr.fit_results[key]])
                # Fit errors
                if corr.fit_results.has_key("fit error estimation"):
                    errors = corr.fit_results["fit error estimation"]
                    for err, par in zip(errors, fitparms):
                        nam, val = mdls.GetHumanReadableParameterDict( 
                                                model.id, [par], [err])
                        Fitting.append(["Err "+nam[0], val[0]])

                InfoDict["fitting"] = Fitting

        ## Normalization parameter id to name
        if corr.normalize_parm is None:
            normparmtext = "None"
        elif Page.normparm < len(corr.fit_parameters):
            normparmtext = corr.fit_model.parameters[0][corr.normalize_parm] 
        else:
            # supplementary parameters
            supnum = corr.normalize_parm - len(corr.fit_parameters)
            normparmtext = MoreInfo[supnum][0]
        Title.append(["Normalization", normparmtext]) 
        
        ## Background
        Background = list()
        if corr.is_cc:
            if len(corr.backgrounds) == 2:
                # Channel 1
                Background.append([ "bg name Ch1", 
                                    corr.backgrounds[0].name])
                Background.append([ "bg rate Ch1 [kHz]", 
                                    corr.backgrounds[0].countrate])
                # Channel 2
                Background.append([ "bg name Ch2", 
                                    corr.backgrounds[1].name])
                Background.append([ "bg rate Ch2 [kHz]", 
                                    corr.backgrounds[1].countrate])
                InfoDict["background"] = Background
        else:
            if len(corr.backgrounds) == 1:
                Background.append([ "bg name", 
                                    corr.backgrounds[0].name])
                Background.append([ "bg rate [kHz]", 
                                    corr.backgrounds[0].countrate])
                InfoDict["background"] = Background
        ## Function doc string
        InfoDict["modeldoc"] = [corr.fit_model.description_long]
        InfoDict["title"] = Title

        return InfoDict


class ShowInfo(wx.Frame):
    def __init__(self, parent):
        # parent is main frame
        self.parent = parent
        # Get the window positioning correctly
        pos = self.parent.GetPosition()
        pos = (pos[0]+100, pos[1]+100)
        wx.Frame.__init__(self, parent=self.parent, title="Info",
                 pos=pos, style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        ## MYID
        # This ID is given by the parent for an instance of this class
        self.MyID = None
        # Page
        self.Page = self.parent.notebook.GetCurrentPage()
        # Size
        initial_size = wx.Size(650,700)
        initial_sizec = (initial_size[0]-6, initial_size[1]-30)
        self.SetMinSize(wx.Size(200,200))
        self.SetSize(initial_size)
        ## Content
        self.panel = wx.Panel(self)
        self.control = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE, 
                        size=initial_sizec)
        self.control.SetEditable(False)
        font1 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Monospace')
        self.control.SetFont(font1)
        btncopy = wx.Button(self.panel, wx.ID_CLOSE, 'Copy to clipboard')
        self.Bind(wx.EVT_BUTTON, self.OnCopy, btncopy)
        self.topSizer = wx.BoxSizer(wx.VERTICAL)
        self.topSizer.Add(btncopy)
        self.topSizer.Add(self.control)
        self.panel.SetSizer(self.topSizer)
        self.topSizer.Fit(self)
        #Icon
        if parent.MainIcon is not None:
            wx.Frame.SetIcon(self, parent.MainIcon)
        self.Show(True)
        wx.EVT_SIZE(self, self.OnSize)
        self.Content()


    def Content(self):
        # Fill self.control with content.
        # Parameters and models
        if self.parent.notebook.GetPageCount() == 0:
            self.control.SetValue("")
            self.panel.Disable()
            return
        self.panel.Enable()
        Page = self.Page
        InfoMan = InfoClass(CurPage=Page)
        PageInfo = InfoMan.GetCurFancyInfo()
        self.control.SetValue(PageInfo)


    def OnClose(self, event=None):
        self.parent.toolmenu.Check(self.MyID, False)
        self.parent.ToolsOpen.__delitem__(self.MyID)
        self.Destroy()


    def OnCopy(self, event):
        if not wx.TheClipboard.IsOpened():
            clipdata = wx.TextDataObject()
            clipdata.SetText(self.control.GetValue())
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()
        else:
            print "Other application has lock on clipboard."


    def OnPageChanged(self, page=None, trigger=None):
        """
            This function is called, when something in the panel
            changes. The variable `trigger` is used to prevent this
            function from being executed to save stall time of the user.
            Forr a list of possible triggers, see the doc string of
            `tools`.
        """
        if trigger in ["parm_batch", "fit_batch", "page_add_batch"]:
            return
        # When parent changes
        self.Page = page
        self.Content()


    def OnSize(self, event):
        size = event.GetSize()
        sizec = wx.Size(size[0]-5, size[1]-30)
        self.panel.SetSize(size)
        self.control.SetSize(sizec)
