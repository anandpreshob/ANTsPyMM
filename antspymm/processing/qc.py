"""
Quality control functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np

# Import ants conditionally
try:
    import ants
except ImportError:
    ants = None


def tsnr( x, mask, indices=None ):
    """
    3D temporal snr image from a 4D time series image ... the matrix is normalized to range of 0,1

    x: image

    mask : mask

    indices: indices to use

    returns a 3D image
    """
    if ants is None:
        raise ImportError("ants package is required for tsnr function")
    
    M = ants.timeseries_to_matrix( x, mask )
    M = M - M.min()
    M = M / M.max()
    if indices is not None:
        M=M[indices,:]
    stdM = np.std(M, axis=0 )
    stdM[np.isnan(stdM)] = 0
    tt = round( 0.975*100 )
    threshold_std = np.percentile( stdM, tt )
    tsnrimage = ants.make_image( mask, stdM )
    return tsnrimage


def dvars( x,  mask, indices=None ):
    """
    dvars on a time series image ... the matrix is normalized to range of 0,1

    x: image

    mask : mask

    indices: indices to use

    returns an array
    """
    if ants is None:
        raise ImportError("ants package is required for dvars function")
    
    M = ants.timeseries_to_matrix( x, mask )
    M = M - M.min()
    M = M / M.max()
    if indices is not None:
        M=M[indices,:]
    DVARS = np.zeros( M.shape[0] )
    for i in range(1, M.shape[0] ):
        vecdiff = M[i-1,:] - M[i,:]
        DVARS[i] = np.sqrt( ( vecdiff * vecdiff ).mean() )
    DVARS[0] = DVARS.mean()
    return DVARS


def mask_snr( x, background_mask, foreground_mask, bias_correct=True ):
    """

    Estimate signal to noise ratio (SNR) in an image using
    a user-defined foreground and background mask.
    Actually estimates the reciprocal of the coefficient of variation.

    Arguments
    ---------

    x : an antsImage

    background_mask : binary antsImage

    foreground_mask : binary antsImage

    bias_correct : boolean

    """
    if ants is None:
        raise ImportError("ants package is required for mask_snr function")
    
    import numpy as np
    if foreground_mask.sum() <= 1 or background_mask.sum() <= 1:
        return 0
    xbc = ants.iMath( x - x.min(), "Normalize" )
    if bias_correct:
        xbc = ants.n3_bias_field_correction( xbc )
    xbc = ants.iMath( xbc - xbc.min(), "Normalize" )
    signal = (xbc[ foreground_mask == 1] ).mean()
    noise = (xbc[ background_mask == 1] ).std()
    return signal / noise


def slice_snr( x,  background_mask, foreground_mask, indices=None ):
    """
    slice-wise SNR on a time series image

    x: image

    background_mask : mask - maybe CSF or background or dilated brain mask minus original brain mask

    foreground_mask : mask - maybe cortex or WM or brain mask

    indices: indices to use

    returns an array
    """
    if ants is None:
        raise ImportError("ants package is required for slice_snr function")
    
    xuse=ants.iMath(x,"Normalize")
    MB = ants.timeseries_to_matrix( xuse, background_mask )
    MF = ants.timeseries_to_matrix( xuse, foreground_mask )
    if indices is not None:
        MB=MB[indices,:]
        MF=MF[indices,:]
    ssnr = np.zeros( MB.shape[0] )
    for i in range( MB.shape[0] ):
        ssnr[i]=MF[i,:].mean()/MB[i,:].std()
    ssnr[np.isnan(ssnr)] = 0
    return ssnr


def foreground_background_snr( x, background_dilation=10,
                                   foreground_dilation=0, its=5 ):
    """

    Estimates simple foreground background SNR where the foreground is estimated
    by the Otsu method and the background is a dilated version of the
    negated foreground.

    Arguments
    ---------

    x : an antsImage

    background_dilation : integer greater than or equal to zero

    foreground_dilation : integer greater than or equal to zero

    its : integer greater than or equal to zero - how many times to apply dilation

    """
    if ants is None:
        raise ImportError("ants package is required for foreground_background_snr function")
    
    if x.dimension > 3:
        x = ants.slice_image( x, axis=3, idx=0 )
    xx = ants.iMath( x - x.min(), 'Normalize' )
    fgmask = ants.get_mask( xx ).iMath("MD",background_dilation,its=its)
    bgmask = ants.threshold_image( fgmask, 0, 0 )
    if foreground_dilation > 0 :
        fgmask = ants.get_mask( xx ).iMath("ME",foreground_dilation,its=its)
    else:
        fgmask = ants.get_mask( xx )
    fgvec = x[ fgmask == 1]
    bgvec = x[ bgmask == 1]
    return ( fgvec.mean() / bgvec.std() )


def quantile_snr( x,
                  background_quantile_lo=0.01,
                  background_quantile_hi=0.10,
                  foreground_quantile=0.99,
                  mask=None ):
    """

    Estimate signal to noise ratio (SNR) in an image using quantiles
    of the intensity distribution (histogram).  The user should be
    aware of how the quantiles will impact identification of "signal"
    and "noise" voxels, in particular, if the image has small or sparse
    signal regions or if the background noise is non-zero but relatively
    constant.

    Arguments
    ---------

    x : an antsImage

    background_quantile_lo : lower quantile for noise

    background_quantile_hi : upper quantile for noise

    foreground_quantile : quantile for signal

    mask : optional mask

    """
    if mask is None:
        xvec = x.numpy().flatten()
    else:
        xvec = x[ mask == 1 ]
    qqlo = np.quantile( xvec, background_quantile_lo )
    qqhi = np.quantile( xvec, background_quantile_hi )
    qqsignal = np.quantile( xvec, foreground_quantile )
    bginds = np.where( ( xvec >= qqlo ) & ( xvec <= qqhi ) )
    signal = qqsignal
    if len( bginds[0] ) > 0:
        noise = xvec[ bginds ].std()
        return signal / noise
    else:
        return 0