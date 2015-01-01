# -*- coding: utf-8 -*-
""" PyCorrFit data set

Classes for FCS data evaluation.
"""
from __future__ import print_function, division


import hashlib
import numpy as np


class Background(object):
    """ A class to unify background handling
    """
    def __init__(self, coutrate=None, duration_s=None, trace=None,
                 identifier=None, name=None):
        """ Initiate a background.
        
        Parameters
        ----------
        coutrate : float
            Average countrate [Hz].
        duration_s : float
            Duration of measurement in seconds.
        trace : 2d `numpy.ndarray` of shape (N,2)
            The trace (time [s], countrate [Hz]).
            Overwrites `average` and `duration_s`
        name : str
            The name of the measurement.
        identifier : str
            A unique identifier. If not given, a sha256 hash will be
            created.
        
        """
        self.coutrate = coutrate
        self.duration_s = duration_s
        self.identifier = identifier
        self.name = name
            
        if trace is not None:
            self.trace = trace
            self.coutrate = np.average(trace[:,1])
            self.duration_s = trace[-1,0] - trace[0,0]
        
        ## Make sure all parameters have sensible values
        if self.duration_s is None:
            self.duration_s = 0
        
        if self.countrate is None:
            self.countrate = 0
        
        if self.trace is None:
            self.trace = np.zeros((2,2))
            self.trace[:,1] = self.countrate
            
        if name is None:
            self.name = "{:.2f kHz, {} s}".format(coutrate/1000,
                                                  self.duration_s)
        if identifier is None:
            hasher = hashlib.sha256()
            hasher.update(str(self.trace))
            hasher.update(self.name)
            self.identifier = hasher.hexdigest()            
            
           

class FCSDataSet(object):
    """ The class has all methods necessary for an FCS measurement.
    
    """
    def __init__(self, ac=None, trace=None, trace2=None,
                  ac2=None, cc12=None, cc21=None,
                  background1=None, background2=None):
        """ Initializes the FCS data set.
        
        All parms are 2d ndarrays of shape (N,2).
        
        """
        self.filename = None
        self.trace1 = trace
        self.trace2 = trace2
        self.ac1 = ac
        self.ac2 = ac2
        self.cc12 = cc12
        self.cc21 = cc21

        if background1 is not None:
            self.background1 = Background(trace = background1)
        if background2 is not None:
            self.background2 = background(trace = background2)

        self.InitComputeDerived()
        self.DoBackgroundCorrection()
        

    def EnableBackgroundCorrection(self, enable=True):
        """ Set to false to disable background correction.
        """
        self.UseBackgroundCorrection = enable
        
        
    def InitComputeDerived(self):
        """ Computes all parameters that can be derived from the
            correlation data and traces themselves.
        """
        # lenght of traces determines auto- or cross-correlation
        if self.cc12 is not None or self.cc21 is not None:
            self.IsCrossCorrelation = True
        else:
            self.IsCrossCorrelation = False
        if self.ac1 is not None or self.ac2 is not None:
            self.IsAutCorrelation = True
        else:
            self.IsAutCorrelation = False
        
        if self.trace1 is not None:
            self.duration1_s = self.trace1[-1,0] - self.trace1[0,0]
            self.countrate1 = np.average(self.trace1[:,1])
        else:
            self.countrate1 = None
            self.duration1_s = None

        if self.trace2 is not None:
            self.duration2_s = self.trace2[-1,0] - self.trace2[0,0]
            self.countrate2 = np.average(self.trace2[:,1])
        else:
            self.duration2_s = None
            self.countrate2 = None            


        # Initial fitting range is entire data set
        self.fit_range = {}
        names = ["ac1", "ac2", "cc12", "cc21"]
        for name in names:
            if hasattr(self, name):
                data = getattr(self, name)
                self.fit_range[name] = (data[0,0], data[-1,0])



    def DoBackgroundCorrection(self, data):
        """ Performs background correction.
        
        Notes
        -----
        Thompson, N. Lakowicz, J.;
        Geddes, C. D. & Lakowicz, J. R. (ed.)
        Fluorescence Correlation Spectroscopy
        Topics in Fluorescence Spectroscopy,
        Springer US, 2002, 1, 337-378
        """
        # Autocorrelation
        if ( not self.countrate1 in [0, None] and
             self.background1 is not None and
             self.ac1 is not None):
            S = self.countrate1
            B = self.background1.countrate
            # Calculate correction factor
            bgfactor = (S/(S-B))**2
            # set plotting data
            self.plot_ac1 = self.ac1 * bgfactor
        if ( not self.countrate2 in [0, None] and
             self.background2 is not None and
             self.ac2 is not None):
            S = self.countrate2
            B = self.background2.countrate
            # Calculate correction factor
            bgfactor = (S/(S-B))**2
            # set plotting data
            self.plot_ac2 = self.ac2 * bgfactor            
        
        # Crosscorrelation
        if ( not self.countrate1 in [0, None] and
             not self.countrate2 in [0, None] and
             self.background1 is not None and
             self.background2 is not None and
             self.IsCrossCorrelation
           )
            S = self.countrate1
            S2 = self.countrate2
            B = self.background1.countrate1
            B2 = self.background1.countrate2
            bgfactor = (S/(S-B)) * (S2/(S2-B2))
            if self.cc12 is not None:
                self.plot_cc12 = self.cc12 * bgfactor 
            if self.cc21 is not None:
                self.plot_cc21 = self.cc21 * bgfactor             
            

    def GetBackground(self):
        """ Returns the backgrounds of the data set.
        """
        return self.background1, self.background2
        
    
    def GetPlotCorrelation(self):
        """ Returns a dictionary with correlation curves.
        
        Keys may include "ac1", "ac2", "cc12", "cc21" as well as
        "ac1_fit", "ac2_fit", "cc12_fit", "cc21_fit".
        """
        if self.UseBackgroundCorrection:
            self.DoBackgroundCorrection()
    
        result = dict()
        
        names = ["ac1", "ac2", "cc12", "cc21"]
        
        for name in names:
            if not hasattr(self, "plot_"+name):
                rawdata = getattr(self, name)
                if rawdata is not None:
                    result[name] = rawdata.copy()
            else:
                plotdata = getattr(self, name)
                result[name] = plotdata.copy()
            if hasattr(self, "plot_"+name+"_fit"):
                fitted = getattr(self, "plot_"+name+"_fit")
                result[name+"_fit"] = fitted.copy()

        return result


    def SetBackground(self, bgac1=None, bgac2=None):
        """ Set the background of the measurement.
        
        `bg*` is an instance of `pycorrfit.Background`.
        """
        #if isinstance(background, Background):
        #    self.background = bg
        #elif isinstance(background, list)
        self.background1 = bgac1
        self.background2 = bgac2


    def SetFitRange(self, start, end, components=None):
        """ Set the range for fitting a correlation curve.
        
        The unit is seconds.
        
        Exapmles
        --------
        SetFitRange(.2, 1)
        SetFitRange(.4, .7, ["ac2", "cc12"])
        """
        if components is not None:
            self.fit_range = {"ac1" : (start,end),
                              "ac2" : (start,end),
                              "cc12": (start,end),
                              "cc21": (start,end)  }
        else:
            for cc in components:
                self.fitrange[cc] = (start,end)
            


class Fit(object):
    """ Used for fitting FCS data to models.
    """
    def __init__(self, raw_data, modelid, modelparms=None, weights=None,
                 fit_range=None, fit_type=None, fit_algorithm="Lev-Mar"):
        """ Using an FCS model, fit the data of shape (N,2).


        fittype - type of fit. Can be one of the following
                  - "None" (standard) - no weights. (*weights* is ignored)
                  - "splineX" - fit a Xth order spline and calulate standard
                               deviation from that difference
                  - "model function" - calculate std. dev. from difference
                                        of fit function and dataexpfull.
                  - "other" - use `weights`
        fit_algorithm - The fitting algorithm to be used for minimization
                        Have a look at the PyCorrFit documentation for more
                        information.
                        - "Lev-Mar" Least squares minimization
                        - "Nelder-Mead" Simplex
                        - "BFGS" quasi-Newton method of Broyden,
                                 Fletcher, Goldfarb and Shanno
                        - "Powell"
                        - "Polak-Ribiere"
                        
                        
        """
        self.y = raw_data[:,1].copy()
        self.x = raw_data[:,0] * 1000 # convert to ms
        
        
        
        
