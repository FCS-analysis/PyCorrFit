import numpy as np
from . import fib4


"""FCS Bulk Correlation Software

    Copyright (C) 2015  Dominic Waithe

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""


def tttr2xfcs (y,num,NcascStart,NcascEnd, Nsub):
    """autocorr, autotime = tttr2xfcs(y,num,10,20)
     Translation into python of:
     Fast calculation of fluorescence correlation data with asynchronous time-correlated single-photon counting.
     Michael Wahl, Ingo Gregor, Matthias Patting, Jorg Enderlein
     """
 
    dt = np.max(y)-np.min(y)
    y = np.round(y[:],0)
    numshape = num.shape[0]
     
    autotime = np.zeros(((NcascEnd+1)*(Nsub+1),1));
    auto = np.zeros(((NcascEnd+1)*(Nsub+1), num.shape[1], num.shape[1])).astype(np.float64)
    shift = float(0)
    delta = float(1)
    
    
    
    for j in range(0,NcascEnd):
        
        #Finds the unique photon times and their indices. The division of 'y' by '2' each cycle makes this more likely.
        
        y,k1 = np.unique(y,1)
        k1shape = k1.shape[0]
        
        #Sums up the photon times in each bin.
        cs =np.cumsum(num,0).T
        
        #Prepares difference array so starts with zero.
        diffArr1 = np.zeros(( k1shape+1));
        diffArr2 = np.zeros(( k1shape+1));
        
        #Takes the cumulative sum of the unique photon arrivals
        diffArr1[1:] = cs[0,k1].reshape(-1)
        diffArr2[1:] = cs[1,k1].reshape(-1)
        
        #del k1
        #del cs
        num =np.zeros((k1shape,2))
        

        
        #Finds the total photons in each bin. and represents as count.
        #This is achieved because we have the indices of each unique time photon and cumulative total at each point.
        num[:,0] = np.diff(diffArr1)
        num[:,1] = np.diff(diffArr2)
        #diffArr1 = [];
        #diffArr2 = [];
        
        for k in range(0,Nsub):
            shift = shift + delta
            lag = np.round(shift/delta,0)
    
            
            #Allows the script to be sped up.
            if j >= NcascStart:
                

                #Old method
                #i1= np.in1d(y,y+lag,assume_unique=True)
                #i2= np.in1d(y+lag,y,assume_unique=True)
                
                #New method, cython
                i1,i2 = fib4.dividAndConquer(y, y+lag,y.shape[0])
                i1 = i1.astype(np.bool);
                i2 = i2.astype(np.bool);
                #Faster dot product method, faster than converting to matrix.
                auto[(k+(j)*Nsub),:,:] = np.dot((num[i1,:]).T,num[i2,:])/delta    
            
            autotime[k+(j)*Nsub] =shift;
        
        #Equivalent to matlab round when numbers are %.5
        y = np.ceil(np.array(0.5*y))
        delta = 2*delta
    
    for j in range(0, auto.shape[0]):
        auto[j,:,:] = auto[j,:,:]*dt/(dt-autotime[j])
    autotime = autotime/1000000
    return auto, autotime


def delayTime2bin(dTimeArr, chanArr, chanNum, winInt):
    
    decayTime = np.array(dTimeArr)
    #This is the point and which each channel is identified.
    decayTimeCh =decayTime[chanArr == chanNum] 
    
    #Find the first and last entry
    firstDecayTime = 0;#np.min(decayTimeCh).astype(np.int32)
    tempLastDecayTime = np.max(decayTimeCh).astype(np.int32)
    
    #We floor this as the last bin is always incomplete and so we discard photons.
    numBins = np.floor((tempLastDecayTime-firstDecayTime)/winInt)
    lastDecayTime = numBins*winInt
    

    bins = np.linspace(firstDecayTime,lastDecayTime, int(numBins)+1)
    
    
    photonsInBin, jnk = np.histogram(decayTimeCh, bins)

    #bins are valued as half their span.
    decayScale = bins[:-1]+(winInt/2)

    #decayScale =  np.arange(0,decayTimeCh.shape[0])
   
    
    

    return list(photonsInBin), list(decayScale)
