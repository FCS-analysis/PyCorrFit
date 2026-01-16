import numpy as np
import numpy.typing as npt


def dividAndConquer(
    arr1: npt.NDArray[np.integer | np.floating],
    arr2: npt.NDArray[np.integer | np.floating],
) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
    """
    Pure numpy implementation of the original
    'divide and conquer fast intersection algorithm. Waithe D 2014'

    # Note
    2026-01-16 Thomas Bischof

    Replaces the following block from fib4.pyx. I tested this against both
    random data and real data, and obtained identical results.
    --------------------------------------------
    PicoQuant functionalities from FCS_viewer

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
        \"\"\"divide and conquer fast intersection algorithm. Waithe D 2014\"\"\"

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
    """
    a1 = arr1[:-1]
    a2 = arr2[:-1]

    idx1 = np.searchsorted(a2, a1)
    idx1[idx1 == len(a2)] = len(a2) - 1
    mask1 = (a1 == a2[idx1]).astype(np.float64)

    idx2 = np.searchsorted(a1, a2)
    idx2[idx2 == len(a1)] = len(a1) - 1
    mask2 = (a2 == a1[idx2]).astype(np.float64)

    return mask1, mask2
