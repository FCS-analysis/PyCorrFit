# -*- coding: utf-8 -*-
"""
PyCorrFit

Module frontend
The frontend displays the GUI (Graphic User Interface).
All functions and modules are called from here.
"""
import numpy as np                      # NumPy
import re
import string
import warnings
import wx                               # GUI interface wxPython
from wx.lib.agw import floatspin        # Float numbers in spin fields
import wx.lib.plot as plot              # Plotting in wxPython
import wx.lib.scrolledpanel as scrolled


from . import models as mdls
from . import tools
from . import fcs_data_set as pcfbase
from .fcs_data_set import Correlation, Fit


def float2string_nsf(fval, n=7):
    """
    Truncate a float to n significant figures and return nice string.
    Arguments:
      q : a float
      n : desired number of significant figures
    Returns:
    String with only n s.f. and trailing zeros.
    """
    #sgn=np.sign(fval)
    if fval == 0:
        npoint=n
    else:
        q=abs(fval)
        k=int(np.ceil(np.log10(q/n)))
        npoint = n-k
    string="{:.{}f}".format(fval, npoint)
    return string

def nice_string(string):
    """
    Convert a string of a float created by `float2string_nsf`
    to something nicer.
    
    i.e.
    - 1.000000 -> 1
    - 1.010000 -> 1.010
    """
    if len(string.split(".")[1].replace("0", "")) == 0:
        return "{:d}".format(int(float(string)))
    else:
        olen = len(string)
        newstring = string.rstrip("0")
        if olen > len(newstring):
            string=newstring+"0"
        return string

class PCFFloatValidator(wx.PyValidator):
    def __init__(self, flag=None, pyVar=None):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return PCFFloatValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        
        for x in val:
            if x not in string.digits:
                return False

        return True

    def OnChar(self, event):
        """
        Filter the characters that are put in the control.
        
        TODO:
        - check for strings that do not make sense
          - 2e-4.4
          - 2e--3
          - 3-1+5
        """
        key = event.GetKeyCode()
        ctrl = event.GetEventObject()
        # Get the actual string from the object
        curval = wx.TextCtrl.GetValue(ctrl)

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        char = chr(key)
        char = char.replace(",", ".")
        
        onlyonce = [".", "e"]
        if char in onlyonce and curval.count(char):
            # not allowed
            return

        if ( char in string.digits or
             char in ["+", "-", ".", "e"]):
            event.Skip()
            return

        if not wx.Validator_IsSilent():
            wx.Bell()

        # Returning without calling event.Skip eats the event before it
        # gets to the text control
        return


class PCFFloatTextCtrl(wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, validator=PCFFloatValidator(), size=(110,-1),
                             style=wx.TE_PROCESS_ENTER, **kwargs)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self._PCFvalue = 0.0

    def OnMouseEnter(self, e):
        self.SetFocus()
        self.SetSelection(-1,0)

    def OnMouseLeave(self, e):
        self.SetSelection(0,0)
        self.SetInsertionPoint(0)

    def SetValue(self, value):
        self._PCFvalue = value
        string = PCFFloatTextCtrl.float2string(value)
        wx.TextCtrl.SetValue(self, string)
    
    def GetValue(self):
        string = wx.TextCtrl.GetValue(self)
        if string == PCFFloatTextCtrl.float2string(self._PCFvalue):
            # use internal value: more accurate
            #print("internal", self._PCFvalue)
            return self._PCFvalue
        else:
            # new value
            #print("external", string)
            return PCFFloatTextCtrl.string2float(string)
        
    @staticmethod
    def float2string(value):
        """
        inverse of string2float with some tweaks
        """
        value = float2string_nsf(value)
        value = nice_string(value)
        return value
        
    @staticmethod
    def string2float(string):
        """
        Remove any characters that are not in
        [+-{0-9},.] and show a decent float
        value.
        """
        # allow comma
        string = string.replace(",", ".")
        # allow only one decimal point
        string = string[::-1].replace(".", "", string.count(".")-1)[::-1]
        try:
            string = "{:.12f}".format(float(string))
        except:
            pass
        # remove letters
        string = re.sub(r'[^\d.-]+', '', string)
        if len(string) == 0:
            string = "0"
        return float(string)



class FittingPanel(wx.Panel):
    """
    Those are the Panels that show the fitting dialogs with the Plots.
    """
    def __init__(self, parent, counter, modelid, active_parms, tau=None):
        """ Initialize with given parameters. """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.parent = parent
        
        self.corr = Correlation(fit_model=modelid)
        if tau is not None:
            self.corr.lag_time = tau
        # active_parameters:
        # [0] labels
        # [1] values
        # [2] bool values to fit
        self.corr.fit_parameters = active_parms[1]
        self.corr.fit_parameters_variable = active_parms[2]

        self._bgselected = None
        self._bg2selected = None

        self.FitKnots = 5 # number of knots for spline fit or similiars

        self.weighted_fittype_id = 0 # integer (drop down item)
        self.weighted_nuvar = 3 # bins for std-dev. (left and rigth)

        
        # The weights that are plotted in the page
        # This is set by the PlotAll function
        self.weights_plot_fill_area = None
        
        # A list containing page numbers that share parameters with this page.
        # This parameter is defined by the global fitting tool and is saved in
        # sessions.
        self.GlobalParameterShare = list()
        # Counts number of Pages already created:
        self.counter = counter
        # Has inital plot been performed?
        # Call PlotAll("init") to set this to true. If it is true, then
        # nothing will be plotted if called with "init"
        self.InitialPlot = False
        # Model we are using

        # Tool statistics uses this list:
        self.StatisticsCheckboxes = None
        ### Splitter window
        # Sizes
        size = parent.notebook.GetSize()
        tabsize = 33
        size[1] = size[1] - tabsize
        self.sizepanelx = 270
        canvasx = size[0]-self.sizepanelx+5
        sizepanel = (self.sizepanelx, size[1])
        sizecanvas = (canvasx, size[1])
        self.sp = wx.SplitterWindow(self, size=size, style=wx.SP_3DSASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.sp.SetMinimumPaneSize(1)
        ## Settings Section (left side)
        #self.panelsettings = wx.Panel(self.sp, size=sizepanel)
        self.panelsettings = scrolled.ScrolledPanel(self.sp, size=sizepanel)
        self.panelsettings.SetupScrolling(scroll_x=False)
        ## Setting up Plot (correlation + chi**2)
        self.spcanvas = wx.SplitterWindow(self.sp, size=sizecanvas,
                                          style=wx.SP_3DSASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.spcanvas.SetMinimumPaneSize(1)
        # y difference in pixels between Auocorrelation and Residuals
        cupsizey = size[1]*4/5
        # Calculate initial data
        self.calculate_corr()
        # Draw the settings section
        self.settings()
        # Load default values
        self.apply_parameters_reverse()
        # Upper Plot for plotting of Correlation Function
        self.canvascorr = plot.PlotCanvas(self.spcanvas)
        self.canvascorr.setLogScale((True, False))  
        self.canvascorr.SetEnableZoom(True)
        self.PlotAll(event="init", trigger="tab_init")
        self.canvascorr.SetSize((canvasx, cupsizey))
        # Lower Plot for plotting of the residuals
        self.canvaserr = plot.PlotCanvas(self.spcanvas)
        self.canvaserr.setLogScale((True, False))
        self.canvaserr.SetEnableZoom(True)
        self.canvaserr.SetSize((canvasx, size[1]-cupsizey))
        self.spcanvas.SplitHorizontally(self.canvascorr, self.canvaserr,
                                        cupsizey)
        self.sp.SplitVertically(self.panelsettings, self.spcanvas,
                                self.sizepanelx)
        # Bind resizing to resizing function.
        wx.EVT_SIZE(self, self.OnSize)

    @property
    def active_parms(self):
        names = self.corr.fit_model.parameters[0]
        parms = self.corr.fit_parameters
        bool = self.corr.fit_parameters_variable
        return [names, parms, bool]

    @property
    def IsCrossCorrelation(self):
        return self.corr.is_cc
    
    @property
    def modelid(self):
        return self.corr.fit_model.id
    
    @property
    def title(self):
        return self.tabtitle.GetValue()

    @title.setter
    def title(self, title):
        self.tabtitle.SetValue(title.strip())
        self.corr.title = title.strip()
    
    @property
    def traceavg(self):
        warnings.warn("Trace average always set to none!")
        return None
    
    @property
    def tracecc(self):
        if self.corr.is_cc and len(self.corr.traces) != 0:
            return self.corr.traces
        else:
            return None

    @property
    def bgselected(self):
        return self._bgselected
    
    @bgselected.setter
    def bgselected(self, value):
        if value is None:
            self.corr.backgrounds=[]
            return
        # check paren.Background and get id
        background = self.parent.Background[value]
        self.corr.background_replace(0, background)
        self._bgselected = value

    @property
    def bg2selected(self):
        return self._bg2selected
    
    @bg2selected.setter
    def bg2selected(self, value):
        if value is None:
            if self.corr.is_cc:
                self.corr.backgrounds=[]
            return
        # check paren.Background and get id
        background = self.parent.Background[value]
        self.corr.background_replace(1, background)
        self._bg2selected = value

    def apply_parameters(self, event=None):
        """ Read the values from the form and write it to the
            pages parameters.
            This function is called when the "Apply" button is hit.
        """
        modelid = self.corr.fit_model.id
        parameters = list()
        parameters_variable = list()
        # Read parameters from form and update self.active_parms[1]
        for i in np.arange(len(self.spincontrol)):
            parameters.append(1*self.spincontrol[i].GetValue())
            parameters_variable.append(self.checkboxes[i].GetValue())

        self.corr.fit_parameters_variable = np.array(parameters_variable,
                                                     dtype=bool)
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # Here: Convert human readable units to program internal
        # units
        parmsconv = mdls.GetInternalFromHumanReadableParm(
                        modelid, np.array(parameters))[1]
        self.corr.fit_parameters = parmsconv

        # Fitting parameters
        self.weighted_nuvar = self.Fitbox[5].GetValue()
        
        self.weighted_fittype_id = self.Fitbox[1].GetSelection()

        fitbox_value = self.Fitbox[1].GetValue()
        
        if self.weighted_fittype_id == -1:
            # User edited knot number
            Knots = fitbox_value
            Knots = filter(lambda x: x.isdigit(), Knots)
            if Knots == "":
                Knots = "5"
            self.weighted_fittype_id = 1
            self.FitKnots = str(Knots)
            fit_weight_type = "spline{}".format(self.FitKnots)
            fit_weight_data = self.weighted_nuvar
        elif self.weighted_fittype_id == 1:
            Knots = fitbox_value
            Knots = filter(lambda x: x.isdigit(), Knots)
            self.FitKnots = int(Knots)
            fit_weight_type = "spline{}".format(self.FitKnots)
            fit_weight_data = self.weighted_nuvar
        elif self.weighted_fittype_id == 0:
            fit_weight_type = "none"
            fit_weight_data = None
        elif self.weighted_fittype_id == 2:
            fit_weight_type = "model function"
            fit_weight_data = self.weighted_nuvar
        else: # fitbox_selection > 2:
            fit_weight_type = fitbox_value
            self.corr.fit_weight_type = fitbox_value
            fit_weight_data = self.corr.fit_weight_data
        
        # Fitting algorithm
        keys = pcfbase.GetAlgorithmStringList()[0]
        idalg = self.AlgorithmDropdown.GetSelection()
        
        self.corr.fit_algorithm = keys[idalg]
        self.corr.fit_weight_type = fit_weight_type
        self.corr.fit_weight_data = fit_weight_data
        
        # If parameters have been changed because of the check_parms
        # function, write them back.
        self.apply_parameters_reverse()


    def apply_parameters_reverse(self, event=None):
        """ Read the values from the pages parameters and write
            it to the form.
        """
        modelid = self.corr.fit_model.id
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        # Here: Convert program internal units to
        # human readable units
        parameters = mdls.GetHumanReadableParms(modelid,
                                        self.corr.fit_parameters)[1]
        parameters_variable = self.corr.fit_parameters_variable
        # Write parameters to the form on the Page
        for i in np.arange(len(self.active_parms[1])):
            self.spincontrol[i].SetValue(parameters[i])
            self.checkboxes[i].SetValue(parameters_variable[i])
        # Fitting parameters
        self.Fitbox[5].SetValue(self.weighted_nuvar)
        idf = self.weighted_fittype_id
        List = self.Fitbox[1].GetItems()
        List[1] = "spline ("+str(self.FitKnots)+" knots)"
        self.Fitbox[1].SetItems(List)
        self.Fitbox[1].SetSelection(idf)
        # Fitting algorithm
        keys = pcfbase.GetAlgorithmStringList()[0]
        idalg = keys.index(self.corr.fit_algorithm)
        self.AlgorithmDropdown.SetSelection(idalg)
        self.updateChi2()


    def calculate_corr(self):
        """ 
        Calculate model correlation function
        """
        return self.corr.modeled


    def Fit_enable_fitting(self):
        """ Enable the fitting button and the weighted fit control"""
        #self.Fitbox = [ fitbox, weightedfitdrop, fittext, fittext2,
        #                fittextvar, fitspin, buttonfit, textalg,
        #                self.AlgorithmDropdown]
        self.Fitbox[0].Enable()
        self.Fitbox[1].Enable()
        self.Fitbox[6].Enable()
        self.Fitbox[7].Enable()
        self.Fitbox[8].Enable()

        
    def Fit_function(self, event=None, noplots=False, trigger=None):
        """ Calls the fit function.
            
            `noplots=True` prevents plotting of spline fits
        
            `trigger` is passed to page.PlotAll.
                      If trigger is "fit_batch", then `noplots` is set
                      to `True`.
        
        """
        # Make a busy cursor
        wx.BeginBusyCursor()
        # Apply parameters
        # This also applies the background correction, if present
        self.apply_parameters()
        # Create instance of fitting class
        
        # TODO:
        # 
        self.GlobalParameterShare = list()

        try:
            Fit(self.corr)
        except ValueError:
            # I sometimes had this on Windows. It is caused by fitting to
            # a .SIN file without selection proper channels first.
            print "There was an Error fitting. Please make sure that you\n"+\
                  "are fitting in a proper channel domain."
            wx.EndBusyCursor()
            raise

        # Update spin-control values
        self.apply_parameters_reverse()
        # Plot everthing
        self.PlotAll(trigger=trigger)
        # update displayed chi2
        self.updateChi2()
        # Return cursor to normal
        wx.EndBusyCursor()


    def Fit_WeightedFitCheck(self, event=None):
        """ Enable Or disable variance calculation, dependent on 
            "Weighted Fit" checkbox
        """
        #self.Fitbox=[ fitbox, weightedfitdrop, fittext, fittext2, fittextvar,
        #                fitspin, buttonfit ]
        weighted = (self.Fitbox[1].GetSelection() != 0)
        # In the case of "Average" we do not enable the
        # "Calculation of variance" part.
        if weighted is True and self.Fitbox[1].GetValue() != "Average":
            self.Fitbox[2].Enable()
            self.Fitbox[3].Enable()
            self.Fitbox[4].Enable()
            self.Fitbox[5].Enable()
        else:
            self.Fitbox[2].Disable()
            self.Fitbox[3].Disable()
            self.Fitbox[4].Disable()
            self.Fitbox[5].Disable()


    def MakeStaticBoxSizer(self, boxlabel):
        """ Create a Box with check boxes (fit yes/no) and possibilities to 
            change initial values for fitting.

            Parameters:
            *boxlabel*: The name of the box (is being displayed)
            *self.active_parms[0]*: A list of things to put into the box

            Returns:
            *sizer*: The static Box
            *check*: The (un)set checkboxes
            *spin*: The spin text fields
        """
        modelid = self.corr.fit_model.id
        box = wx.StaticBox(self.panelsettings, label=boxlabel)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        check = list()
        spin = list()
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        labels = mdls.GetHumanReadableParms(modelid,
                                            self.corr.fit_parameters)[0]
        for label in labels:
            sizerh = wx.BoxSizer(wx.HORIZONTAL)
            checkbox = wx.CheckBox(self.panelsettings, label=label)
            # We needed to "from wx.lib.agw import floatspin" to get this:
            spinctrl = PCFFloatTextCtrl(self.panelsettings)
            sizerh.Add(spinctrl)
            sizerh.Add(checkbox)
            sizer.Add(sizerh)
            # Put everything into lists to be able to refer to it later
            check.append(checkbox)
            spin.append(spinctrl)
        return sizer, check, spin


    def OnAmplitudeCheck(self, event=None):
        """ Enable/Disable BG rate text line.
            New feature introduced in 0.7.8
        """
        modelid = self.corr.fit_model.id
        ## Normalization to a certain parameter in plots
        # Find all parameters that start with an "N"
        # ? and "C" ?
        # Create List
        normlist = list()
        normlist.append("None")
        ## Add parameters
        parameterlist = list()
        for i in np.arange(len(self.active_parms[0])):
            label = self.active_parms[0][i]
            if label[0].lower() == "n":
                normlist.append("*"+label)
                parameterlist.append(i)
        ## Add supplementary parameters
        # Get them from models
        supplement = mdls.GetMoreInfo(modelid, self)
        if supplement is not None:
            for i in np.arange(len(supplement)):
                label = supplement[i][0]
                if label[0].lower() == "n":
                    normlist.append("*"+label)
                    # Add the id of the supplement starting at the
                    # number of fitting parameters of current page.
                    parameterlist.append(i+len(self.active_parms[0]))
        normsel = self.AmplitudeInfo[2].GetSelection()
        if normsel in [0, -1]:
            # init or no normalization selected
            self.corr.normparm = None
            normsel = 0 
        else:
            self.corr.normparm = parameterlist[normsel-1]

        if len(parameterlist) > 0:
            self.AmplitudeInfo[2].Enable()
            self.AmplitudeInfo[3].Enable()
        else:
            self.AmplitudeInfo[2].Disable()
            self.AmplitudeInfo[3].Disable()
        # Set dropdown values
        self.AmplitudeInfo[2].SetItems(normlist)
        self.AmplitudeInfo[2].SetSelection(normsel)
        ## Plot intensities
        # Quick reminder:
        #self.AmplitudeInfo = [ [intlabel1, intlabel2],
        #                       [bgspin1, bgspin2],
        #                       normtoNDropdown, textnor]
        # Signal
        self.AmplitudeInfo[0][0].SetValue("{:.4f}".format(0))
        self.AmplitudeInfo[0][1].SetValue("{:.4f}".format(0))
        for i in range(len(self.corr.traces)):
            S = self.corr.traces[i].countrate
            self.AmplitudeInfo[0][i].SetValue("{:.4f}".format(S))
        if self.corr.is_cc:
            self.AmplitudeInfo[0][1].Enable()
        else:
            self.AmplitudeInfo[0][1].Disable()
        # Background
        ## self.parent.Background[self.bgselected][i]
        ## [0] average signal [kHz]
        ## [1] signal name (edited by user)
        ## [2] signal trace (tuple) ([ms], [kHz])
        if len(self.corr.backgrounds) >= 1:
            self.AmplitudeInfo[1][0].SetValue(
                        self.corr.backgrounds[0].countrate)
        else:
            self.AmplitudeInfo[1][0].SetValue(0)
            self.AmplitudeInfo[1][1].SetValue(0)
        
        if len(self.corr.backgrounds) == 2:
            self.AmplitudeInfo[1][1].SetValue(
                        self.corr.backgrounds[1].countrate)
        else:
            self.AmplitudeInfo[1][1].SetValue(0)
        # Disable the second line in amplitude correction, if we have
        # autocorrelation only.
        boolval = self.corr.is_cc
        for item in self.WXAmplitudeCCOnlyStuff:
            item.Enable(boolval)


    def OnBGSpinChanged(self, e):
        """ Calls tools.background.ApplyAutomaticBackground
            to update background information
        """
        # Quick reminder:
        #self.AmplitudeInfo = [ [intlabel1, intlabel2],
        #                       [bgspin1, bgspin2],
        #                       normtoNDropdown, textnor]
        if self.corr.is_cc:
            # update both self.bgselected and self.bg2selected
            bg = [self.AmplitudeInfo[1][0].GetValue(),
                  self.AmplitudeInfo[1][1].GetValue()]
            tools.background.ApplyAutomaticBackground(self, bg,
                                                      self.parent)
        else:
            # Only update self.bgselected 
            bg = self.AmplitudeInfo[1][0].GetValue()
            tools.background.ApplyAutomaticBackground(self, bg,
                                                      self.parent)
        e.Skip()

    
    def OnTitleChanged(self, e):
        modelid = self.corr.fit_model.id
        pid = self.parent.notebook.GetPageIndex(self)
        if self.tabtitle.GetValue() == "":
            text = self.counter + mdls.modeldict[modelid][1]
        else:
            # How many characters of the the page title should be displayed
            # in the tab? We choose 9: AC1-012 plus 2 whitespaces
            text = self.counter + self.tabtitle.GetValue()[-9:]
        self.parent.notebook.SetPageText(pid,text)        

        
    def OnSetRange(self, e):
        """ Open a new Frame where the parameter range can be set.
            Rewrites self.parameter_range
            Parameter ranges are treated like parameters: They are saved in
            sessions and applied in batch mode.
        """
        # TODO:
        # - make range selector work with new class
        
        # We write a separate tool for that.
        # This tool does not show up in the Tools menu.
        if self.parent.RangeSelector is None:
            self.parent.RangeSelector = tools.RangeSelector(self)
            self.parent.RangeSelector.Bind(wx.EVT_CLOSE,
                                           self.parent.RangeSelector.OnClose)
        else:
            try:
                self.parent.RangeSelector.OnClose()
            except:
                pass
            self.parent.RangeSelector = None
        

    def OnSize(self, event):
        """ Resize the fitting Panel, when Window is resized. """
        size = self.parent.notebook.GetSize()
        tabsize = 33
        size[1] = size[1] - tabsize
        self.sp.SetSize(size)


    def PlotAll(self, event=None, trigger=None):
        """
        This function plots the whole correlation and residuals canvas.
        We do:
        - Channel selection
        - Background correction
        - Apply Parameters (separate function)
        - Drawing of plots
        
        The `event` is usually just an event from buttons or similar
        wx objects. It can be "init", then some initial plotting is
        done before the data is handled.
        
        The `trigger` is passed to `self.parent.OnFNBPageChanged` so
        that tools can update their content accordingly. For more
        information on triggers, have a look at the doctring of the
        `tools` submodule.
        """
        if event == "init":
            # We use this to have the page plotted at least once before
            # readout of parameters (e.g. startcrop, endcrop)
            # This is a performence tweak.
            if self.InitialPlot:
                return
            else:
                self.InitialPlot = True
        ## Enable/Disable, set values frontend normalization
        self.OnAmplitudeCheck()
        ## Apply parameters
        self.apply_parameters()
        # Calculate correlation function from parameters
        ## Drawing of correlation plot
        # Plots corr.correlation_fit and the calcualted correlation function 
        # self.datacorr into the upper canvas.
        # Create a line @ y=zero:
        zerostart = self.corr.lag_time_fit[0]
        zeroend = self.corr.lag_time_fit[-1]
        datazero = [[zerostart, 0], [zeroend,0]]
        # Set plot colors
        width = 1   
        colexp = "grey"  
        colfit = "blue"
        colweight = "cyan"
        lines = list()
        linezero = plot.PolyLine(datazero, colour='orange', width=width)
        lines.append(linezero)
        if self.corr.correlation is not None:
            if self.corr.is_weighted_fit and \
               self.parent.MenuShowWeights.IsChecked():
                try:
                    weights = self.corr.fit_results["fit weights"]
                except:
                    weights = self.corr.fit_weight_data
                
                if isinstance(weights, np.ndarray):
                    # user might have selected a new weight type and
                    # presses apply, do not try to display weights

                    # if weights are from average or other, make sure that the 
                    # dimensions are correct
                    if weights.shape[0] == self.corr.correlation.shape[0]:
                        weights = weights[self.corr.fit_ival[0]:self.corr.fit_ival[1]]
                        
                    if np.allclose(weights, np.ones_like(weights)):
                        weights = 0
                    if weights.shape[0] != self.corr.modeled_fit.shape[0]:
                        # non-matching weigths
                        warnings.warn("Unmatching weights found. Probably from previous data set.")
                        weights = 0

                    # Add the weights to the graph.
                    # This is done by drawing two lines.
                    w = 1*self.corr.modeled_fit
                    w1 = 1*w
                    w2 = 1*w
                    
                    w1[:, 1] = w[:, 1] + weights
                    w2[:, 1] = w[:, 1] - weights
                    # crop w1 and w2 if corr.correlation_fit does not include all
                    # data points.
                    if np.all(w[:,0] == self.corr.correlation_fit[:,0]):
                        pass
                    else:
                        raise ValueError("This should not have happened: size of weights is wrong.")
                    ## Normalization with self.normfactor
                    w1[:,1] *= self.corr.normalize_factor
                    w2[:,1] *= self.corr.normalize_factor
                    self.weights_plot_fill_area = [w1,w2]
                    lineweight1 = plot.PolyLine(w1, legend='',
                                              colour=colweight, width=width)
                    lines.append(lineweight1)
                    lineweight2 = plot.PolyLine(w2, legend='',
                                              colour=colweight, width=width)
                    lines.append(lineweight2)
            else:
                self.weights_plot_fill_area = None
                
            ## Plot Correlation curves
            # Plot both, experimental and calculated data
            # Normalization with self.normfactor, new feature in 0.7.8
            datacorr_norm = self.corr.modeled_plot
            linecorr = plot.PolyLine(datacorr_norm, legend='', colour=colfit,
                                     width=width)
            dataexp_norm = self.corr.correlation_plot
            lineexp = plot.PolyLine(dataexp_norm, legend='', colour=colexp,
                                    width=width)
            # Draw linezero first, so it is in the background
            lines.append(lineexp)
            lines.append(linecorr)
            PlotCorr = plot.PlotGraphics(lines, 
                                xLabel=u'lag time τ [ms]', yLabel=u'G(τ)')
            self.canvascorr.Draw(PlotCorr)
            ## Calculate residuals
            resid_norm = self.corr.residuals_plot
            lineres = plot.PolyLine(resid_norm, legend='', colour=colfit,
                                    width=width)
            
            # residuals or weighted residuals?
            if self.corr.is_weighted_fit:
                yLabelRes = "weighted \nresiduals"
            else:
                yLabelRes = "residuals"
            PlotRes = plot.PlotGraphics([linezero, lineres], 
                                   xLabel=u'lag time τ [ms]',
                                   yLabel=yLabelRes)
            self.canvaserr.Draw(PlotRes)
        else:
            # Amplitude normalization, new feature in 0.7.8
            datacorr_norm = self.corr.modeled_plot
            linecorr = plot.PolyLine(datacorr_norm, legend='', colour='blue',
                                     width=1)
            PlotCorr = plot.PlotGraphics([linezero, linecorr],
                       xLabel=u'Lag time τ [ms]', yLabel=u'G(τ)')
            self.canvascorr.Draw(PlotCorr)
        self.parent.OnFNBPageChanged(trigger=trigger)


    def settings(self):
        """ Here we define, what should be displayed at the left side
            of the fitting page/tab.
            Parameters:
        """
        modelid = self.corr.fit_model.id
        horizontalsize = self.sizepanelx-10
        # Title
        # Create empty tab title
        mddat = mdls.modeldict[modelid]
        modelshort = mdls.GetModelType(modelid)
        titlelabel = u"Data set ({} {})".format(modelshort, mddat[1])
        boxti = wx.StaticBox(self.panelsettings, label=titlelabel)
        sizerti = wx.StaticBoxSizer(boxti, wx.VERTICAL)
        sizerti.SetMinSize((horizontalsize, -1))
        self.tabtitle = wx.TextCtrl(self.panelsettings, value="", 
                                    size=(horizontalsize-20, -1))
        self.Bind(wx.EVT_TEXT, self.OnTitleChanged, self.tabtitle)
        sizerti.Add(self.tabtitle)                       
        # Create StaticBoxSizer
        box1, check, spin = self.MakeStaticBoxSizer("Model parameters")
        # Make the check boxes and spin-controls available everywhere
        self.checkboxes = check
        self.spincontrol = spin
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        labels, parameters = mdls.GetHumanReadableParms(modelid,
                                                self.active_parms[1])
        parameterstofit = self.active_parms[2]
        # Set initial values given by user/programmer for Diffusion Model
        for i in np.arange(len(labels)):
            self.checkboxes[i].SetValue(parameterstofit[i]) 
            self.spincontrol[i].SetValue(parameters[i])
        # Put everything together
        self.panelsettings.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panelsettings.sizer.Add(sizerti)
        self.panelsettings.sizer.Add(box1)
        # Add button "Apply" and "Set range"
        horzs = wx.BoxSizer(wx.HORIZONTAL)
        buttonapply = wx.Button(self.panelsettings, label="Apply")
        self.Bind(wx.EVT_BUTTON, self.PlotAll, buttonapply)
        horzs.Add(buttonapply)
        buttonrange = wx.Button(self.panelsettings, label="Set range")
        self.Bind(wx.EVT_BUTTON, self.OnSetRange, buttonrange)
        horzs.Add(buttonrange)
        box1.Add(horzs)
        # Set horizontal size
        box1.SetMinSize((horizontalsize, -1))
        ## More info
        normbox = wx.StaticBox(self.panelsettings, label="Amplitude corrections")
        miscsizer = wx.StaticBoxSizer(normbox, wx.VERTICAL)
        miscsizer.SetMinSize((horizontalsize, -1))
        # Intensities and Background
        sizeint = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)
        sizeint.Add(wx.StaticText(self.panelsettings, label="[kHz]"))
        sizeint.Add(wx.StaticText(self.panelsettings,
                    label="Intensity"))
        sizeint.Add(wx.StaticText(self.panelsettings,
                    label="Background"))
        sizeint.Add(wx.StaticText(self.panelsettings, label="Ch1"))
        intlabel1 = wx.TextCtrl(self.panelsettings)
        bgspin1 = PCFFloatTextCtrl(self.panelsettings)
        bgspin1.Bind(wx.EVT_KILL_FOCUS, self.OnBGSpinChanged)
        bgspin1.Bind(wx.EVT_TEXT_ENTER, self.OnBGSpinChanged)
        sizeint.Add(intlabel1)
        intlabel1.SetEditable(False)
        sizeint.Add(bgspin1)
        chtext2 = wx.StaticText(self.panelsettings, label="Ch2")
        sizeint.Add(chtext2)
        intlabel2 = wx.TextCtrl(self.panelsettings)
        intlabel2.SetEditable(False)
        bgspin2 = PCFFloatTextCtrl(self.panelsettings)
        bgspin2.Bind(wx.EVT_KILL_FOCUS, self.OnBGSpinChanged)
        sizeint.Add(intlabel2)
        sizeint.Add(bgspin2)
        miscsizer.Add(sizeint)
        ## Normalize to n?
        textnor = wx.StaticText(self.panelsettings, label="Plot normalization")
        miscsizer.Add(textnor)
        normtoNDropdown = wx.ComboBox(self.panelsettings)
        self.Bind(wx.EVT_COMBOBOX, self.PlotAll, normtoNDropdown)
        miscsizer.Add(normtoNDropdown)
        self.AmplitudeInfo = [ [intlabel1, intlabel2],
                               [bgspin1, bgspin2],
                                normtoNDropdown, textnor]
        self.WXAmplitudeCCOnlyStuff = [chtext2, intlabel2, bgspin2]
        self.panelsettings.sizer.Add(miscsizer)
        ## Add fitting Box
        fitbox = wx.StaticBox(self.panelsettings, label="Fitting options")
        fitsizer = wx.StaticBoxSizer(fitbox, wx.VERTICAL)
        fitsizer.SetMinSize((horizontalsize, -1))
        # Add a checkbox for weighted fitting
        weightedfitdrop = wx.ComboBox(self.panelsettings)
        self.weightlist = ["no weights", "spline (5 knots)", "model function"]
        weightedfitdrop.SetItems(self.weightlist)
        weightedfitdrop.SetSelection(0)
        fitsizer.Add(weightedfitdrop)
        # WeightedFitCheck() Enables or Disables the variance part
        weightedfitdrop.Bind(wx.EVT_COMBOBOX, self.Fit_WeightedFitCheck)
        # Add the variance part.
        # In order to do a weighted fit, we need to calculate the variance
        # at each point of the experimental data array.
        # In order to do that, we need to know how many data points from left
        # and right of the interesting data point we want to include in that
        # calculation.
        fittext = wx.StaticText(self.panelsettings, 
                                label="Calculation of the variance")
        fitsizer.Add(fittext)
        fittext2 = wx.StaticText(self.panelsettings, 
                                 label="from 2j+1 data points")
        fitsizer.Add(fittext2)
        fitsizerspin = wx.BoxSizer(wx.HORIZONTAL)
        fittextvar = wx.StaticText(self.panelsettings, label="j = ")
        fitspin = wx.SpinCtrl(self.panelsettings, -1, initial=3, min=1, max=100)
        fitsizerspin.Add(fittextvar)
        fitsizerspin.Add(fitspin)
        fitsizer.Add(fitsizerspin)
        # Add algorithm selection
        textalg = wx.StaticText(self.panelsettings, label="Algorithm")
        fitsizer.Add(textalg)
        self.AlgorithmDropdown = wx.ComboBox(self.panelsettings)
        items = pcfbase.GetAlgorithmStringList()[1]
        self.AlgorithmDropdown.SetItems(items)
        self.Bind(wx.EVT_COMBOBOX, self.apply_parameters,
                  self.AlgorithmDropdown)
        fitsizer.Add(self.AlgorithmDropdown)
        self.AlgorithmDropdown.SetMaxSize(weightedfitdrop.GetSize())
        # Add button "Fit" and chi2 display
        fitbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonfit = wx.Button(self.panelsettings, label="Fit")
        self.Bind(wx.EVT_BUTTON, self.Fit_function, buttonfit)
        fitbuttonsizer.Add(buttonfit)
        self.WXTextChi2 = wx.StaticText(self.panelsettings)
        # this StaticText is updated by `self.updateChi2()`
        fitbuttonsizer.Add(self.WXTextChi2, flag=wx.ALIGN_CENTER)
        fitsizer.Add(fitbuttonsizer)
        self.panelsettings.sizer.Add(fitsizer)
        # Squeeze everything into the sizer
        self.panelsettings.SetSizer(self.panelsettings.sizer)
        # This is also necessary in Windows
        self.panelsettings.Layout()
        self.panelsettings.Show()
        # Make all the stuff available for everyone
        self.Fitbox = [ fitbox, weightedfitdrop, fittext, fittext2,
                        fittextvar, fitspin, buttonfit, textalg,
                        self.AlgorithmDropdown]
        # Disable Fitting since no data has been loaded yet
        for element in self.Fitbox:
            element.Disable()
        self.panelsettings.sizer.Fit(self.panelsettings)
        self.parent.Layout()


    def updateChi2(self):
        """
        updates the self.WXTextChi2 text control
        """
        label = u""
        if hasattr(self.corr, "fit_results"):
            if "chi2" in self.corr.fit_results:
                chi2 = self.corr.fit_results["chi2"]
                chi2str = float2string_nsf(chi2, n=3)
                chi2str = nice_string(chi2str)
                label = u"  χ²={}".format(chi2str)
        # This does not work with wxPython 2.8.12:
        #self.WXTextChi2.SetLabelMarkup(u"<b>{}</b>".format(label))
        self.WXTextChi2.SetLabel(u"{}".format(label))

        
        
        
        