"""PyCorrFit data set: Classes for FCS data evaluation"""
import hashlib

import numpy as np
import scipy.integrate as spintg


class Trace(object):
    """ unifies trace handling
    """
    def __init__(self, trace=None, countrate=None, duration=None,
                 name=None):
        """ Load trace data
        
        Parameters
        ----------
        trace : ndarray of shape (N, 2)
            The array contains time [ms] and count rate [kHz].
        coutrate : float
            Average count rate [kHz].
            Mandatory if `trace` is None. 
        duration : float
            Duration of measurement in milliseconds.
            Mandatory if `trace` is None.
        name : str
            The name of the trace.
        """
        self._countrate = None
        self._duration = None
        self._trace = None
        self._uid = None
        
        if trace is None:
            self.countrate = countrate
            self.duration = duration
        else:
            self.trace = trace
        
        if name is None:
            name = "{:.2f}kHz, {:.0f}s".format(self.countrate,
                                               self.duration/1000)
        self.name = name
    
    def __getitem__(self, idx):
        return self.trace[idx]
    
    def __repr__(self):
        text = "Trace of length {:.3f}s and countrate {:.3f}kHz".format(
                self.duration/1000, self.countrate)
        return text
    
    @property
    def countrate(self):
        if self._countrate is None:
            #self._countrate = np.average(self._trace[:,1])
            # Take into account traces that have arbitrary sampling
            self._countrate = spintg.simps(self._trace[:,1], self._trace[:,0]) / self.duration
        return self._countrate
    
    @countrate.setter
    def countrate(self, value):
        if value is None:
            raise ValueError("Setting value to `None` not allowed!")
        if self._trace is not None:
            raise ValueError("Cannot set countrate; `self.trace` is set.")
        self._countrate = value

    @property
    def duration(self):
        if not hasattr(self, "_duration") or self._duration is None:
            self._duration = self._trace[-1,0] - self._trace[0,0]
        return self._duration
    
    @duration.setter
    def duration(self, value):
        if value is None:
            raise ValueError("Setting value to `None` not allowed!")
        if self._trace is not None:
            raise ValueError("Cannot set duration; `self.trace` is set.")
        self._duration = value
    
    @property
    def uid(self):
        if self._uid is None:
            hasher = hashlib.sha256()
            hasher.update(str(np.random.random()))
            hasher.update(str(self.trace))
            hasher.update(self.name)
            self._uid = hasher.hexdigest()
        return self._uid
    
    @property
    def trace(self):
        if self._trace is None:
            self._trace = np.array([ [0,             self.countrate],
                                     [self.duration, self.countrate] 
                                    ])
        return self._trace
    
    @trace.setter
    def trace(self, value):
        if value is None:
            raise ValueError("Setting value to `None` not allowed!")
        if not isinstance(value, np.ndarray):
            raise ValueError("Trace data must be np.ndarray!")
        if value.shape[1] != 2:
            raise ValueError("Shape of array must be (N,2)!")
        self._trace = value
        # self.countrate is set automagically
