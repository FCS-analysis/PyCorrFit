# -*- coding: utf-8 -*-
""" PyCorrFit
    Paul Müller, Biotec - TU Dresden

    Module frontend
    The frontend displays the GUI (Graphic User Interface). All necessary 
    functions and modules are called from here.

    Dimensionless representation:
    unit of time        : 1 ms
    unit of inverse time: 10³ /s
    unit of distance    : 100 nm
    unit of Diff.coeff  : 10 µm²/s
    unit of inverse area: 100 /µm²
    unit of inv. volume : 1000 /µm³
"""
# Use DEMO for contrast-rich screenshots.
# This enlarges axis text and draws black lines instead of grey ones.
DEMO = False


import os
import wx                               # GUI interface wxPython
import wx.lib.plot as plot              # Plotting in wxPython
import numpy as np                      # NumPy
import sys                              # System stuff

import doc
import edclasses                    # Cool stuf like better floatspin
import leastsquaresfit as fit       # For fitting
import models as mdls


## On Windows XP I had problems with the unicode Characters.
# I found this at 
# http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
# and it helped:
reload(sys)
sys.setdefaultencoding('utf-8')


class FittingPanel(wx.Panel):
    """
    Those are the Panels that show the fitting dialogs with the Plots.
    """
    def __init__(self, parent, counter, modelid, active_parms, tau):
        """ Initialize with given parameters. """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.parent = parent
        self.filename = "None"
        ## If this value is set to True, the trace and traceavg variables
        ## will not be used. Instead tracecc a list, of traces will be used.
        self.IsCrossCorrelation = False
        ## Setting up variables for plotting
        self.trace = None        # The intensity trace, tuple
        self.traceavg = None     # Average trace intensity
        self.tracecc = None      # List of traces (in CC mode only)
        self.bgselected = None   # integer, index for parent.Background
        self.bgcorrect = 1.      # Background correction factor for dataexp
        self.normparm = None     # Parameter number used for graph normalization
        self.normfactor = 1.     # Graph normalization factor (e.g. value of n)
        self.startcrop = None    # Where cropping of dataexp starts
        self.endcrop = None      # Where cropping of dataexp ends
        self.dataexp = None      # Experimental data (cropped)
        self.dataexpfull = None  # Experimental data (not cropped)
        self.datacorr = None     # Calculated data
        self.resid = None        # Residuals
        self.data4weight = None  # Data used for weight calculation 
        # Fitting:
        #self.Fitbox=[ fitbox, weightedfitdrop, fittext, fittext2, fittextvar,
        #                fitspin, buttonfit ]
        # chi squared - is also an indicator, if something had been fitted
        self.FitKnots = 5 # number of knots for spline fit or similiars
        self.chi2 = None
        self.weighted_fit_was_performed = False # default is no weighting
        self.weights_used_for_fitting = None # weights used for fitting
        self.weights_used_for_plotting = None # weights used for plotting
        self.weights_plot_fill_area = None # weight area in plot
        self.weighted_fittype_id = None # integer (drop down item)
        self.weighted_fittype = "Unknown" # type of fit used
        self.weighted_nuvar = None # bins for std-dev. (left and rigth)
        # dictionary for alternative variances from e.g. averaging
        self.external_std_weights = dict()
        # Errors of fit dictionary
        self.parmoptim_error = None
        # A list containing page numbers that share parameters with this page.
        # This parameter is defined by the global fitting tool and is saved in
        # sessions.
        self.GlobalParameterShare = list()
        # Counts number of Pages already created:
        self.counter = counter
        # Model we are using
        self.modelid = modelid
        # modelpack:
        # [0] labels
        # [1] values
        # [2] bool values to fit
        # [3] labels human readable (optional)
        # [4] factors human readable (optional)
        modelpack = mdls.modeldict[modelid]
        # The string of the model in the menu
        self.model = modelpack[1]
        # Some more useless text about the model
        self.modelname = modelpack[2]
        # Function for fitting
        self.active_fct = modelpack[3]
        # Parameter verification function.
        # This checks parameters concerning their physical meaningfullness :)
        self.check_parms = mdls.verification[modelid]
        # active_parameters:
        # [0] labels
        # [1] values
        # [2] bool values to fit
        self.active_parms = active_parms
        # Some timescale
        self.taufull = tau
        self.tau = 1*self.taufull
        # Tool statistics uses this list:
        self.StatisticsCheckboxes = None
        ### Splitter window
        # Sizes
        size = parent.notebook.GetSize()
        tabsize = 33
        size[1] = size[1] - tabsize
        self.sizepanelx = 250
        canvasx = size[0]-self.sizepanelx
        sizepanel = (self.sizepanelx, size[1])
        sizecanvas = (canvasx, size[1])
        self.sp = wx.SplitterWindow(self, size=size, style=wx.SP_3DSASH)
        # This is necessary to prevent "Unsplit" of the SplitterWindow:
        self.sp.SetMinimumPaneSize(1)
        ## Settings Section (left side)
        self.panelsettings = wx.Panel(self.sp, size=sizepanel)
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
        # Upper Plot for plotting of Correlation Function
        self.canvascorr = plot.PlotCanvas(self.spcanvas)
        self.canvascorr.setLogScale((True, False))  
        self.canvascorr.SetEnableZoom(True)
        self.PlotAll()
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
        ## Check out the DEMO option and make change the plot:
        try:
            if DEMO == True:
                self.canvascorr.SetFontSizeAxis(16)
                self.canvaserr.SetFontSizeAxis(16)
        except:
            # Don't raise any unnecessary erros
            pass
        # Bind resizing to resizing function.
        wx.EVT_SIZE(self, self.OnSize)


    def apply_parameters(self, event=None):
        """ Read the values from the form and write it to the
            pages parameters.
            This function is called when the "Apply" button is hit.
        """
        parameters = list()
        # Read parameters from form and update self.active_parms[1]
        for i in np.arange(len(self.active_parms[1])):
            parameters.append(1*self.spincontrol[i].GetValue())
            self.active_parms[2][i] = self.checkboxes[i].GetValue()
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # Here: Convert human readable units to program internal
        # units
        e, self.active_parms[1] = mdls.GetInternalFromHumanReadableParm(
                                  self.modelid, np.array(parameters))
        self.active_parms[1] = self.check_parms(1*self.active_parms[1])
        # Fitting parameters
        self.weighted_nuvar = self.Fitbox[5].GetValue()
        self.weighted_fittype_id = self.Fitbox[1].GetSelection()
        if self.Fitbox[1].GetSelection() == -1:
            # User edited knot number
            Knots = self.Fitbox[1].GetValue()
            Knots = filter(lambda x: x.isdigit(), Knots)
            if Knots == "":
                Knots = "5"
            self.weighted_fittype_id = 1
            self.FitKnots = str(Knots)
        elif self.Fitbox[1].GetSelection() == 1:
            Knots = self.Fitbox[1].GetValue()
            Knots = filter(lambda x: x.isdigit(), Knots)
            self.FitKnots = int(Knots)
        # If parameters have been changed because of the check_parms
        # function, write them back.
        self.apply_parameters_reverse()


    def apply_parameters_reverse(self, event=None):
        """ Read the values from the pages parameters and write
            it to the form.
        """
        # check parameters
        self.active_parms[1] = self.check_parms(self.active_parms[1])
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        # Here: Convert program internal units to
        # human readable units
        labels, parameters = \
                     mdls.GetHumanReadableParms(self.modelid,
                                        self.active_parms[1])
        # Write parameters to the form on the Page
        for i in np.arange(len(self.active_parms[1])):
            self.spincontrol[i].SetValue(parameters[i])
            self.checkboxes[i].SetValue(self.active_parms[2][i])
        # Fitting parameters
        self.Fitbox[5].SetValue(self.weighted_nuvar)
        idf = self.weighted_fittype_id
        List = self.Fitbox[1].GetItems()
        List[1] = "Spline ("+str(self.FitKnots)+" knots)"
        self.Fitbox[1].SetItems(List)
        self.Fitbox[1].SetSelection(idf)


    def calculate_corr(self):
        """ Calculate correlation function
            Returns an array of tuples (tau, correlation)
            *self.active_f*: A function that is being calculated using
            *self.active_parms*: A list of parameters
    
            Uses variables:
            *self.datacorr*: Plotting data (tuples) of the correlation curve
            *self.dataexp*: Plotting data (tuples) of the experimental curve
            *self.tau*: "tau"-values for plotting (included) in dataexp.
    
            Returns:
            Nothing. Recalculation of the mentioned global variables is done.
        """
        parameters = self.active_parms[1]
        # calculate correlation values
        y = self.active_fct(parameters, self.tau)
        # Create new plotting data
        self.datacorr = np.zeros((len(self.tau), 2))
        self.datacorr[:, 0] = self.tau
        self.datacorr[:, 1] = y


    def crop_data(self):
        """ Crop the pages data for plotting
            This will create slices from
            *self.taufull* and *self.dataexpfull* using the values from
            *self.startcrop* and *self.endcrop*, creating
            *self.tau* and *self.dataexp*.
        """
        if self.dataexpfull is not None:
            if self.startcrop == self.endcrop:
                # self.bgcorrect is background correction
                self.dataexp = 1*self.dataexpfull
                self.taufull = self.dataexpfull[:,0]
                self.tau = 1*self.taufull
                self.startcrop = 0
                self.endcrop = len(self.taufull)
            else:
                self.dataexp = 1*self.dataexpfull[self.startcrop:self.endcrop]
                self.taufull = self.dataexpfull[:,0]
                self.tau = 1*self.dataexp[:,0]
                # If startcrop is larger than the lenght of dataexp,
                # We will not have an array. Prevent that.
                if len(self.tau) == 0:
                    self.tau = 1*self.taufull
                    self.dataexp = 1*self.dataexpfull
            try:
                self.taufull[self.startcrop]
                self.taufull[self.endcrop-1]
            except:
                self.startcrop = 0
                self.endcrop = len(self.taufull)
                self.tau = 1*self.taufull
                self.dataexp = 1*self.dataexpfull
        else:
            # We have to check if the startcrop and endcrop parameters are
            # inside the taufull array.
            try:
                # Raises IndexError if index out of bounds
                self.taufull[self.startcrop]
                # Raises TypeError if self.endcrop is not an int.
                self.taufull[self.endcrop-1]
            except (IndexError, TypeError):
                self.tau = 1*self.taufull
                self.endcrop = len(self.taufull)
                self.startcrop = 0
            else:
                self.tau = 1*self.taufull[self.startcrop:self.endcrop]
        ## ## Channel selection
        ## # Crops the array *self.dataexpfull* from *start* (int) to *end* (int)
        ## # and assigns the result to *self.dataexp*. If *start* and *end* are 
        ## # equal (or not given), *self.dataexp* will be equal to 
        ## # *self.dataexpfull*.
        ## self.parent.OnFNBPageChanged(e=None, Page=self)



    def CorrectDataexp(self, dataexp):
        """ Background correction
            Background correction with *self.bgcorrect*.
            Overwrites *self.dataexp*.
            For details see:
            Incollection (Thomps:bookFCS2002)
            Thompson, N. Lakowicz, J.; Geddes, C. D. & Lakowicz, J. R. (ed.)
            Fluorescence Correlation Spectroscopy
            Topics in Fluorescence Spectroscopy, Springer US, 2002, 1, 337-378
        """
        # Make a copy. Do not overwrite the original.
        if dataexp is not None:
            modified = 1 * dataexp
            if self.bgselected is not None:
                # self.bgselected - background, needs to be imported via Tools
                if self.traceavg is not None:
                    S = self.traceavg
                    B = self.parent.Background[self.bgselected][0]
                    # Calculate correction factor
                    self.bgcorrect = (S/(S-B))**2
                    # self.dataexp should be set, since we have self.trace
                    modified[:,1] *= self.bgcorrect
            return modified
        else:
            return None

    def Fit_enable_fitting(self):
        """ Enable the fitting button and the weighted fit control"""
        #self.Fitbox=[ fitbox, weightedfitdrop, fittext, fittext2, fittextvar,
        #                fitspin, buttonfit ]
        self.Fitbox[0].Enable()
        self.Fitbox[1].Enable()
        self.Fitbox[-1].Enable()


    def Fit_create_instance(self, noplots=False):
        """ *noplots* prohibits plotting (e.g. splines) """
        ### If you change anything here, make sure you
        ### take a look at the global fit tool!
        ## Start fitting class and fill with information.
        self.apply_parameters()
        Fitting = fit.Fit()
        # Verbose mode?
        if noplots is False:
            Fitting.verbose = self.parent.MenuVerbose.IsChecked()
        Fitting.uselatex = self.parent.MenuUseLatex.IsChecked()
        Fitting.check_parms = self.check_parms
        Fitting.dataexpfull = self.CorrectDataexp(self.dataexpfull)
      ## This is now done in apply_parameters
      #  if self.Fitbox[1].GetSelection() == -1:
      #      # User edited knot number
      #      Knots = self.Fitbox[1].GetValue()
      #      Knots = filter(lambda x: x.isdigit(), Knots)
      #      if Knots == "":
      #          Knots = "5"
      #      List = self.Fitbox[1].GetItems()
      #      List[1] = "Spline ("+Knots+" knots)"
      #      Fitting.fittype = "spline"+Knots
      #      self.Fitbox[1].SetItems(List)
      #      self.Fitbox[1].SetSelection(1)
      #      self.FitKnots = Knots
        if self.Fitbox[1].GetSelection() == 1:
      #      Knots = self.Fitbox[1].GetValue()
      #      Knots = filter(lambda x: x.isdigit(), Knots)
      #      self.FitKnots = Knots
            Fitting.fittype = "spline"+str(self.FitKnots)
            self.parent.StatusBar.SetStatusText("You can change the number"+
               " of knots. Check 'Preference>Verbose Mode' to view the spline.")
        elif self.Fitbox[1].GetSelection() == 2:
            Fitting.fittype = "model function"
            if self is self.parent.notebook.GetCurrentPage():
                self.parent.StatusBar.SetStatusText("This is iterative. Press"+
                 " 'Fit' multiple times. If it does not converge, use splines.")
        elif self.Fitbox[1].GetSelection() > 2:
            # This means we have some user defined std, for example from
            # averaging. This std is stored in self.external_std_weights
            # list, which looks like this:
            # self.external_std_weights["from average"] = 1D np.array std
            Fitting.fittype = "other"
            Fitlist = self.Fitbox[1].GetItems()
            FitValue = Fitlist[self.Fitbox[1].GetSelection()]
            Fitting.external_deviations = self.external_std_weights[FitValue]
            # Fitting will crop the variances according to
            # the Fitting.interval that we set below.
            if self is self.parent.notebook.GetCurrentPage():
                self.parent.StatusBar.SetStatusText("")
        else:
            self.parent.StatusBar.SetStatusText("")
        Fitting.function = self.active_fct
        Fitting.interval = [self.startcrop, self.endcrop]
        Fitting.values = 1*self.active_parms[1]
        Fitting.valuestofit = 1*self.active_parms[2]
        Fitting.weights = self.Fitbox[5].GetValue()
        Fitting.ApplyParameters()
        # Set weighted_fit_was_performed variables
        if self.Fitbox[1].GetSelection() == 0:
            self.weighted_fit_was_performed = False
            self.weights_used_for_fitting = None
            self.tauweight = None
        else:
            self.weighted_fit_was_performed = True
            self.weights_used_for_fitting = Fitting.dataweights
        self.weighted_fittype_id = idf = self.Fitbox[1].GetSelection()
        self.weighted_fittype = self.Fitbox[1].GetItems()[idf]
        return Fitting

        
    def Fit_function(self, event=None, noplots=False):
        """ Call the fit function. """
        # Make a busy cursor
        wx.BeginBusyCursor()
        # Apply parameters
        # This also applies the background correction, if present
        self.apply_parameters()
        # Create instance of fitting class
        Fitting = self.Fit_create_instance(noplots)
        # Reset page counter
        self.GlobalParameterShare = list()
        try:
            Fitting.least_square()
        except ValueError:
            # I sometimes had this on Windows. It is caused by fitting to
            # a .SIN file without selection proper channels first.
            print "There was an Error fitting. Please make sure that you\n"+\
                  "are fitting in a proper channel domain."
            wx.EndBusyCursor()
            return
        parms = Fitting.valuesoptim
        # create an error dictionary
        p_error = Fitting.parmoptim_error
        if p_error is None:
            self.parmoptim_error = None
        else:
            self.parmoptim_error = dict()
            errcount = 0
            for i in np.arange(len(parms)):
                if self.active_parms[2][i]:
                    self.parmoptim_error[self.active_parms[0][i]] =p_error[errcount]
                    errcount += 1
        self.chi2 = Fitting.chi
        for i in np.arange(len(parms)):
            self.active_parms[1][i] = parms[i]
        # We need this for plotting
        self.calculate_corr()
        self.data4weight = 1.*self.datacorr
        # Update spin-control values
        self.apply_parameters_reverse()
        # Plot everthing
        self.PlotAll()
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
        box = wx.StaticBox(self.panelsettings, label=boxlabel)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        check = list()
        spin = list()
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        labels, parameters = mdls.GetHumanReadableParms(self.modelid,
                                                self.active_parms[1])
        for label in labels:
            sizerh = wx.BoxSizer(wx.HORIZONTAL)
            checkbox = wx.CheckBox(self.panelsettings, label=label)
            # We needed to "from wx.lib.agw import floatspin" to get this:
            spinctrl = edclasses.FloatSpin(self.panelsettings, digits=10,
                                           increment=.01)
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
        #self.AmplitudeInfo = [ bgnorm, bgtex, normtoNDropdown, textnor]
        ## Normalization to a certain parameter in plots
        # Find all parameters that start with an "N"
        # ? and "C" ?
        # Create List
        normlist = list()
        normlist.append("None")
        # Add parameters
        parameterlist = list()
        for i in np.arange(len(self.active_parms[0])):
            label = self.active_parms[0][i]
            if label[0] == "n" or label[0] == "N":
                normlist.append("*"+label)
                parameterlist.append(i)
        normsel = self.AmplitudeInfo[2].GetSelection()
        if event == "init":
            # Read everything from the page not from the panel
            # self.normparm was set and we need to set
            #  self.normfactor
            #  self.AmplitudeInfo[2]
            if self.normparm is not None:
                self.normfactor =  self.active_parms[1][self.normparm]
                for j in np.arange(len(parameterlist)):
                    if parameterlist[j] == self.normparm:
                        normsel = j+1
            else:
                self.normfactor = 1.
                normsel = 0
        else:
            if normsel > 0:
                # Make sure we are not normalizing with a background
                parameterid = parameterlist[normsel-1]
                self.normfactor = self.active_parms[1][parameterid]
                # For parameter export:
                self.normparm = parameterlist[parameterid]
                # No internal parameters will be changed
                # Only the plotting
            else:
                self.normfactor = 1.
                normsel = 0
                # For parameter export
                self.normparm = None
        if len(parameterlist) > 0:
            self.AmplitudeInfo[2].Enable()
            self.AmplitudeInfo[3].Enable()
        else:
            self.AmplitudeInfo[2].Disable()
            self.AmplitudeInfo[3].Disable()
        # Set dropdown values
        self.AmplitudeInfo[2].SetItems(normlist)
        self.AmplitudeInfo[2].SetSelection(normsel)
        ## Background correction
        bgsel = self.AmplitudeInfo[0].GetSelection()
        # Standard is the background of the page
        # Read bg selection
        if event == "init":
            # Read everything from the page not from the panel
            if self.bgselected is not None:
                bgsel = self.bgselected + 1
            else:
                bgsel = 0
        else:
            if bgsel <= 0:
                self.bgselected = None
                bgsel = 0 #None
            else:
                self.bgselected = bgsel - 1
        # Rebuild itemlist
        # self.parent.Background[self.bgselected][i]
        # [0] average signal [kHz]
        # [1] signal name (edited by user)
        # [2] signal trace (tuple) ([ms], [kHz])
        bglist = list()
        bglist.append("None")
        for item in self.parent.Background:
            bgname = item[1]+" (%.2f kHz)" %item[0]
            bglist.append(bgname)
        self.AmplitudeInfo[0].SetItems(bglist)
        self.AmplitudeInfo[0].SetSelection(bgsel)
        #self.AmplitudeInfo = [ bgnorm, bgtex, normtoNDropdown, textnor]
        if len(bglist) <= 1:
            self.AmplitudeInfo[0].Disable()
            self.AmplitudeInfo[1].Disable()
        else:
            self.AmplitudeInfo[0].Enable()
            self.AmplitudeInfo[1].Enable()



    def OnSize(self, event):
        """ Resize the fitting Panel, when Window is resized. """
        size = self.parent.notebook.GetSize()
        tabsize = 33
        size[1] = size[1] - tabsize
        self.sp.SetSize(size)


    def PlotAll(self, event=None):
        """
        This function plots the whole correlation and residuals canvas.
        We do:
        - Channel selection
        - Background correction
        - Apply Parameters (separate function)
        - Drawing of plots
        """
        ## Enable/Disable, set values frontend normalization
        self.OnAmplitudeCheck()
        self.crop_data()
        ## Calculate trace average
        if self.trace is not None:
            # Average of the current pages trace
            self.traceavg = self.trace[:,1].mean()
        # Perform Background correction
        self.dataexp = self.CorrectDataexp(self.dataexp)
        ## Apply parameters
        self.apply_parameters()
        # Calculate correlation function from parameters
        self.calculate_corr()
        ## Drawing of correlation plot
        # Plots self.dataexp and the calcualted correlation function 
        # self.datacorr into the upper canvas.
        # Create a line @ y=zero:
        zerostart = self.tau[0]
        zeroend = self.tau[-1]
        datazero = [[zerostart, 0], [zeroend,0]]
        ## Check out the DEMO option and make change the plot:
        try:
            if DEMO == True:
                width = 4
                colexp = "black"
                colfit = "red"
            else:
                width = 1
                colexp = "grey"
                colfit = "blue"
        except:
            # Don't raise any unnecessary erros
            width = 1   
            colexp = "grey"  
            colfit = "blue"
        colweight = "cyan"
        lines = list()
        linezero = plot.PolyLine(datazero, colour='orange', width=width)
        lines.append(linezero)
                
        if self.dataexp is not None:
            if self.weighted_fit_was_performed == True and \
               self.weights_used_for_fitting is not None and \
               self.parent.MenuShowWeights.IsChecked() and \
               self.data4weight is not None:
                # Add the weights to the graph.
                # This is done by drawing two lines.
                w = 1*self.data4weight
                w1 = 1*w
                w2 = 1*w
                w1[:, 1] = w[:, 1] + self.weights_used_for_fitting 
                w2[:, 1] = w[:, 1] - self.weights_used_for_fitting 
                wend = 1*self.weights_used_for_fitting 
                # crop w1 and w2 if self.dataexp does not include all
                # data points.
                if np.all(w[:,0] == self.dataexp[:,0]):
                    pass
                else:
                    start = np.min(self.dataexp[:,0])
                    end = np.max(self.dataexp[:,0])
                    idstart = np.argwhere(w[:,0]==start)
                    idend = np.argwhere(w[:,0]==end)
                    if len(idend) == 0:
                        # dataexp is longer, do not change anything
                        pass
                    else:
                        w1 = w1[:idend[0][0]+1]
                        w2 = w2[:idend[0][0]+1]
                        wend = wend[:idend[0][0]+1]
                    if len(idstart) == 0:
                        # dataexp starts earlier, do not change anything
                        pass
                    else:
                        w1 = w1[idstart[0][0]:]
                        w2 = w2[idstart[0][0]:]
                        wend = wend[idstart[0][0]:]
                ## Normalization with self.normfactor
                w1[:,1] *= self.normfactor
                w2[:,1] *= self.normfactor
                self.weights_used_for_plotting = wend
                self.weights_plot_fill_area = [w1,w2]
                lineweight1 = plot.PolyLine(w1, legend='',
                                          colour=colweight, width=width)
                lines.append(lineweight1)
                lineweight2 = plot.PolyLine(w2, legend='',
                                          colour=colweight, width=width)
                lines.append(lineweight2)
                
            ## Plot Correlation curves
            # Plot both, experimental and calculated data
            # Normalization with self.normfactor, new feature in 0.7.8
            datacorr_norm = 1*self.datacorr
            datacorr_norm[:,1] *= self.normfactor
            dataexp_norm = 1*self.dataexp
            dataexp_norm[:,1] *= self.normfactor
            linecorr = plot.PolyLine(datacorr_norm, legend='', colour=colfit,
                                     width=width)
            lineexp = plot.PolyLine(dataexp_norm, legend='', colour=colexp,
                                    width=width)
            # Draw linezero first, so it is in the background
            lines.append(lineexp)
            lines.append(linecorr)
            PlotCorr = plot.PlotGraphics(lines, 
                                xLabel='lag time τ [ms]', yLabel='G(τ)')
            self.canvascorr.Draw(PlotCorr)
            ## Calculate residuals
            self.resid = np.zeros((len(self.tau), 2))
            self.resid[:, 0] = self.tau
            self.resid[:, 1] = self.dataexp[:, 1] - self.datacorr[:, 1]
            # Plot residuals
            # Normalization with self.normfactor, new feature in 0.7.8
            resid_norm = np.zeros((len(self.tau), 2))
            resid_norm[:, 0] = self.tau
            resid_norm[:, 1] = dataexp_norm[:, 1] - datacorr_norm[:, 1]
            lineres = plot.PolyLine(resid_norm, legend='', colour=colfit,
                                    width=width)
            # residuals or weighted residuals?
            if self.weighted_fit_was_performed:
                yLabelRes = "weighted \nresiduals"
            else:
                yLabelRes = "residuals"
            PlotRes = plot.PlotGraphics([linezero, lineres], 
                                   xLabel='lag time τ [ms]',
                                   yLabel=yLabelRes)
            self.canvaserr.Draw(PlotRes)
        else:
            # Amplitude normalization, new feature in 0.7.8
            datacorr_norm = 1*self.datacorr
            datacorr_norm[:,1] *= self.normfactor
            linecorr = plot.PolyLine(datacorr_norm, legend='', colour='blue',
                                     width=1)
            PlotCorr = plot.PlotGraphics([linezero, linecorr],
                       xLabel='Lag time τ [ms]', yLabel='G(τ)')
            self.canvascorr.Draw(PlotCorr)
        self.parent.OnFNBPageChanged()


    def settings(self):
        """ Here we define, what should be displayed at the left side
            of the window.
            Parameters:
        """
        # Title
        # Create empty tab title
        boxti = wx.StaticBox(self.panelsettings, label="filename/title")
        sizerti = wx.StaticBoxSizer(boxti, wx.VERTICAL)
        self.tabtitle = wx.TextCtrl(self.panelsettings, value="", 
                                    size=(self.sizepanelx-20, -1))
        sizerti.Add(self.tabtitle)                       
        # Create StaticBoxSizer
        box1, check, spin = self.MakeStaticBoxSizer("Fit parameters")
        # Make the check boxes and spin-controls available everywhere
        self.checkboxes = check
        self.spincontrol = spin
        #
        # As of version 0.7.5: we want the units to be displayed
        # human readable - the way they are displayed 
        # in the Page info tool.
        # 
        labels, parameters = mdls.GetHumanReadableParms(self.modelid,
                                                self.active_parms[1])
        parameterstofit = self.active_parms[2]
        # Set initial values given by user/programmer for Diffusion Model
        for i in np.arange(len(labels)):
            self.checkboxes[i].SetValue(parameterstofit[i]) 
            self.spincontrol[i].SetValue(parameters[i])
            self.spincontrol[i].increment()
        # Put everything together
        self.panelsettings.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panelsettings.sizer.Add(sizerti)
        self.panelsettings.sizer.Add(box1)
        # Add button "Apply"
        buttonapply = wx.Button(self.panelsettings, label="Apply")
        self.Bind(wx.EVT_BUTTON, self.PlotAll, buttonapply)
        # Add it to the parameters box
        box1.Add(buttonapply)
        ## More info
        normbox = wx.StaticBox(self.panelsettings, label="Amplitude parameters")
        miscsizer = wx.StaticBoxSizer(normbox, wx.VERTICAL)
        # Type of normalization
        bgtex = wx.StaticText(self.panelsettings, label="Background correction")
        miscsizer.Add(bgtex)
        bgnorm = wx.ComboBox(self.panelsettings)
        self.Bind(wx.EVT_COMBOBOX, self.PlotAll, bgnorm)
        miscsizer.Add(bgnorm)
        ## Normalize to n?
        textnor = wx.StaticText(self.panelsettings, label="Normalize graph to:")
        miscsizer.Add(textnor)
        normtoNDropdown = wx.ComboBox(self.panelsettings)
        self.Bind(wx.EVT_COMBOBOX, self.PlotAll, normtoNDropdown)
        miscsizer.Add(normtoNDropdown)
        self.AmplitudeInfo = [ bgnorm, bgtex, normtoNDropdown, textnor]
        self.panelsettings.sizer.Add(miscsizer)
        ## Add fitting Box
        fitbox = wx.StaticBox(self.panelsettings, label="Data fitting")
        fitsizer = wx.StaticBoxSizer(fitbox, wx.VERTICAL)
        # Add a checkbox for weighted fitting
        weightedfitdrop = wx.ComboBox(self.panelsettings)
        self.weightlist = ["No weights", "Spline (5 knots)", "Model function"]
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
                                label="Calculation of Variance.")
        fitsizer.Add(fittext)
        fittext2 = wx.StaticText(self.panelsettings, 
                                 label="Include j points from left and right,")
        fitsizer.Add(fittext2)
        fitsizerspin = wx.BoxSizer(wx.HORIZONTAL)
        fittextvar = wx.StaticText(self.panelsettings, label="j = ")
        fitspin = wx.SpinCtrl(self.panelsettings, -1, initial=3, min=1, max=100)
        fitsizerspin.Add(fittextvar)
        fitsizerspin.Add(fitspin)
        fitsizer.Add(fitsizerspin)
        # Add button "Fit"
        buttonfit = wx.Button(self.panelsettings, label="Fit")
        self.Bind(wx.EVT_BUTTON, self.Fit_function, buttonfit)
        fitsizer.Add(buttonfit)
        self.panelsettings.sizer.Add(fitsizer)
        # Squeeze everything into the sizer
        self.panelsettings.SetSizer(self.panelsettings.sizer)
        # This is also necessary in Windows
        self.panelsettings.Layout()
        self.panelsettings.Show()
        # Make all the stuff available for everyone
        self.Fitbox = [ fitbox, weightedfitdrop, fittext, fittext2, fittextvar,
                        fitspin, buttonfit ]
        # Disable Fitting since no data has been loaded yet
        for element in self.Fitbox:
            element.Disable()

