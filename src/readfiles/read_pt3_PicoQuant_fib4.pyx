# -*- coding: utf-8 -*-
""" PicoQuant functionalities from FCS_viewer

This file contains a fast implementation of an algorithm that is
very important (yes I have no clue about the structure of pt3 files)
for importing *.pt3 files: `dividAndConquer`.

The code was written by
Dr. Dominic Waithe
Wolfson Imaging Centre.
Weatherall Institute of Molecular Medicine.
University of Oxford

https://github.com/dwaithe/FCS_viewer

See Also:
    The wrapper: `read_pt3_PicoQuant.py`
    The wrapped file: `read_pt3_PicoQuant_original_FCSViewer.py`.
"""

import cython
cimport cython

import numpy as np
cimport numpy as np

DTYPE = np.float64
ctypedef np.float64_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
def dividAndConquer(arr1b,arr2b,arrLength):
    """divide and conquer fast intersection algorithm. Waithe D 2014"""
    
    cdef np.ndarray[DTYPE_t, ndim=1] arr1bool = np.zeros((arrLength-1))
    cdef np.ndarray[DTYPE_t, ndim=1] arr2bool = np.zeros((arrLength-1))
    cdef np.ndarray[DTYPE_t, ndim=1] arr1 = arr1b
    cdef np.ndarray[DTYPE_t, ndim=1] arr2 = arr2b
    
    cdef int arrLen 
    arrLen = arrLength;
    cdef int i
    i = 0;
    cdef int j 
    j = 0;
   
    while(i <arrLen-1 and j< arrLen-1):
       
        if(arr1[i] < arr2[j]):
          i+=1;
        elif(arr2[j] < arr1[i]):
          j+=1;
        elif (arr1[i] == arr2[j]):
        
          arr1bool[i] = 1;
          arr2bool[j] = 1;
          i+=1;
    
    return arr1bool,arr2bool
