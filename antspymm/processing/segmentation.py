"""
Segmentation functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np

# Import conditionally
try:
    import ants
except ImportError:
    ants = None


def segment_timeseries_by_bvalue(bvals):
    """
    Segments a time series based on a threshold applied to b-values.
    
    This function categorizes indices of the given b-values array into two groups:
    one for indices where b-values are above a near-zero threshold, and another
    where b-values are at or below this threshold. The threshold is set to 1e-12.
    
    Parameters:
    - bvals (numpy.ndarray): An array of b-values.

    Returns:
    - dict: A dictionary with two keys, 'largerbvals' and 'lowbvals', each containing
      the indices of bvals where the b-values are above and at/below the threshold, respectively.
    """
    # Define the threshold
    threshold = 1e-12
    def find_min_value(data):
        if isinstance(data, list):
            return min(data)
        elif isinstance(data, np.ndarray):
            return np.min(data)
        else:
            raise TypeError("Input must be either a list or a numpy array")

    # Get indices where b-values are greater than the threshold
    lowermeans = list(np.where(bvals > threshold)[0])
    
    # Get indices where b-values are less than or equal to the threshold
    highermeans = list(np.where(bvals <= threshold)[0])
    
    if len(highermeans) == 0:
        minval = find_min_value( bvals )
        lowermeans = list(np.where(bvals > minval )[0])
        highermeans = list(np.where(bvals <= minval)[0])

    return {
        'largerbvals': lowermeans,
        'lowbvals': highermeans
    }


def segment_timeseries_by_meanvalue( image, quantile = 0.995 ):
    """
    Identify indices of a time series where we assume there is a different mean
    intensity over the volumes.  The indices of volumes with higher and lower
    intensities is returned.  Can be used to automatically identify B0 volumes
    in DWI timeseries.

    Arguments
    ---------
    image : antsImage with n-frames

    quantile : quantile to use for deciding which volumes have higher values

    returns
    ---------
    dict containing lowermeans and highermeans where volumes at indices in
    lowermeans have lower intensity on average and volumes at indices in
    highermeans have higher intensity on average
    """
    if ants is None:
        raise ImportError("ants package is required for segment_timeseries_by_meanvalue function")
    
    import numpy as np
    meanvalues = []
    if image.dimension == 4:
        nslice = image.shape[3]
        locmask = ants.get_mask( ants.slice_image( image, axis=3, idx=0 ), cleanup = 0 )
        slicer = lambda imgnd, i : ants.slice_image( imgnd, axis=3, idx=i )
    elif image.dimension == 3:
        nslice = image.shape[2]
        locmask = ants.get_mask( ants.slice_image( image, axis=2, idx=0 ), cleanup = 0 )
        slicer = lambda imgnd, i : ants.slice_image( imgnd, axis=2, idx=i )
    else:
        raise ValueError("Image must be 3D or 4D timeseries")
    locmask = locmask.numpy()
    for k in range(nslice):
        temp = slicer( image, k )
        meanvalues.append( temp[locmask==1].mean()  )
    meanvalues = np.asarray( meanvalues )
    qval = np.quantile( meanvalues, quantile )
    lowermeans = list(np.where(meanvalues <= qval)[0])
    highermeans = list(np.where(meanvalues > qval)[0])
    return { 'lowermeans':lowermeans, 'highermeans': highermeans }