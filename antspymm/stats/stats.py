"""
Stats functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# despike_time_series_afni - 60 lines
def despike_time_series_afni(image, c1=2.5, c2=4):
    """
    Despike a time series image using L1 polynomial fitting and nonlinear filtering.
    Based on afni 3dDespike

    :param image: ANTsPy image object containing time series data.
    :param c1: Spike threshold value. Default is 2.5.
    :param c2: Upper range of allowed deviation. Default is 4.
    :return: Despiked ANTsPy image object.
    """
    data = image.numpy()  # Convert to numpy array
    despiked_data = np.copy(data)  # Create a copy for despiked data
    curve = despiked_data * 0.0

    def l1_fit_polynomial(time_series, degree=2):
        """
        Fit a polynomial of given degree to the time series using least squares.
        
        :param time_series: 1D numpy array of voxel time series data.
        :param degree: Degree of the polynomial to fit.
        :return: Fitted polynomial values for the time series.
        """
        t = np.arange(len(time_series))
        coefs = np.polyfit(t, time_series, degree)
        polynomial = np.polyval(coefs, t)
        return polynomial

    # L1 fit a smooth-ish curve to each voxel time series
    # Curve fitting for each voxel
    for x in range(data.shape[0]):
        for y in range(data.shape[1]):
            for z in range(data.shape[2]):
                voxel_time_series = data[x, y, z, :]
                curve[x, y, z, :] = l1_fit_polynomial(voxel_time_series, degree=2)

    # Compute the MAD of the residuals
    residuals = data - curve
    mad = np.median(np.abs(residuals - np.median(residuals, axis=-1, keepdims=True)), axis=-1, keepdims=True)
    sigma = np.sqrt(np.pi / 2) * mad
    # Ensure sigma is not zero to avoid division by zero
    sigma_safe = np.where(sigma == 0, 1e-10, sigma)

    # Optionally, handle NaN or inf values in data, curve, or sigma
    data = np.nan_to_num(data, nan=0.0, posinf=np.finfo(np.float64).max, neginf=np.finfo(np.float64).min)
    curve = np.nan_to_num(curve, nan=0.0, posinf=np.finfo(np.float64).max, neginf=np.finfo(np.float64).min)
    sigma_safe = np.nan_to_num(sigma_safe, nan=1e-10, posinf=np.finfo(np.float64).max, neginf=np.finfo(np.float64).min)

    # Despike algorithm
    spike_counts = np.zeros( image.shape[3] )
    for i in range(data.shape[-1]):
        s = (data[..., i] - curve[..., i]) / sigma_safe[..., 0]
        ww = s > c1
        s_prime = np.where( ww, c1 + (c2 - c1) * np.tanh((s - c1) / (c2 - c1)), s)
        spike_counts[i] = ww.sum()
        despiked_data[..., i] = curve[..., i] + s_prime * sigma[..., 0]

    # Convert back to ANTsPy image
    despiked_image = ants.from_numpy(despiked_data)
    return ants.copy_image_info( image, despiked_image ), spike_counts



# despike_time_series - 39 lines
def despike_time_series(image, threshold=3.0, replacement='threshold' ):
    """
    Despike a time series image.
    
    :param image: ANTsPy image object containing time series data.
    :param threshold: z-score value to identify spikes. Default is 3.
    :param replacement: median or threshold - the latter is similar 3DDespike but simpler
    :return: Despiked ANTsPy image object.
    """
    # Convert image to numpy array
    data = image.numpy()
    
    # Calculate the mean and standard deviation along the time axis
    mean = np.mean(data, axis=-1)
    std = np.std(data, axis=-1)

    # Identify spikes: points where the deviation from the mean exceeds the threshold
    spikes = np.abs(data - mean[..., np.newaxis]) > threshold * std[..., np.newaxis]

    # Replace spike values
    spike_counts = np.zeros( image.shape[3] )
    for i in range(data.shape[-1]):
        slice = data[..., i]
        spike_locations = spikes[..., i]
        spike_counts[i] = spike_locations.sum()
        if replacement == 'median':
            slice[spike_locations] = np.median(slice)  # Replace with median or another method
        else:
	    # Calculate threshold values (mean ± threshold * std)
            threshold_values = mean + np.sign(slice - mean) * threshold * std
            slice[spike_locations] = threshold_values[spike_locations]
        data[..., i] = slice
    # Convert back to ANTsPy image
    despike_image = ants.from_numpy(data)
    despike_image = ants.copy_image_info( image, despike_image )
    return despike_image, spike_counts





# spec_taper - 36 lines
def spec_taper(x, p=0.1):
    from scipy import stats, signal, fft
    from statsmodels.regression.linear_model import yule_walker
    """
    Computes a tapered version of x, with tapering p.

    Adapted from R's stats::spec.taper at https://github.com/telmo-correa/time-series-analysis/blob/master/Python/spectrum.py

    """

    p = np.r_[p]
    assert np.all((p >= 0) & (p < 0.5)), "'p' must be between 0 and 0.5"

    x = np.r_[x].astype('float64')
    original_shape = x.shape

    assert len(original_shape) <= 2, "'x' must have at most 2 dimensions"
    while len(x.shape) < 2:
        x = np.expand_dims(x, axis=1)

    nr, nc = x.shape
    if len(p) == 1:
        p = p * np.ones(nc)
    else:
        assert len(p) == nc, "length of 'p' must be 1 or equal the number of columns of 'x'"

    for i in range(nc):
        m = int(np.floor(nr * p[i]))
        if m == 0:
            continue
        w = 0.5 * (1 - np.cos(np.pi * np.arange(1, 2 * m, step=2)/(2 * m)))
        x[:, i] = np.r_[w, np.ones(nr - 2 * m), w[::-1]] * x[:, i]

    x = np.reshape(x, original_shape)
    return x



# spec_ci - 20 lines
def spec_ci(df, coverage=0.95):
    from scipy import stats, signal, fft
    from statsmodels.regression.linear_model import yule_walker
    """
    Computes the confidence interval for a spectral fit, based on the number of degrees of freedom.

    Adapted from R's stats::plot.spec at https://github.com/telmo-correa/time-series-analysis/blob/master/Python/spectrum.py

    """

    assert coverage >= 0 and coverage < 1, "coverage probability out of range [0, 1)"

    tail = 1 - coverage

    phi = stats.chi2.cdf(x=df, df=df)
    upper_quantile = 1 - tail * (1 - phi)
    lower_quantile = tail * phi

    return df / stats.chi2.ppf([upper_quantile, lower_quantile], df=df)



# spec_pgram - 86 lines
def spec_pgram(x, xfreq=1, spans=None, kernel=None, taper=0.1, pad=0, fast=True, demean=False, detrend=True,
               plot=True, **kwargs):
    """
    Computes the spectral density estimate using a periodogram.  Optionally, it also:
    - Uses a provided kernel window, or a sequence of spans for convoluted modified Daniell kernels.
    - Tapers the start and end of the series to avoid end-of-signal effects.
    - Pads the provided series before computation, adding pad*(length of series) zeros at the end.
    - Pads the provided series before computation to speed up FFT calculation.
    - Performs demeaning or detrending on the series.
    - Plots results.

    Implemented to ensure compatibility with R's spectral functions, as opposed to reusing scipy's periodogram.

    Adapted from R's stats::spec.pgram at https://github.com/telmo-correa/time-series-analysis/blob/master/Python/spectrum.py

    example:

    import numpy as np
    import antspymm
    myx = np.random.rand(100,1)
    myspec = antspymm.spec_pgram(myx,0.5)

    """
    from scipy import stats, signal, fft
    from statsmodels.regression.linear_model import yule_walker
    def daniell_window_modified(m):
        """ Single-pass modified Daniell kernel window.

        Weight is normalized to add up to 1, and all values are the same, other than the first and the
        last, which are divided by 2.
        """
        def w(k):
            return np.where(np.abs(k) < m, 1 / (2*m), np.where(np.abs(k) == m, 1/(4*m), 0))

        return w(np.arange(-m, m+1))

    N0 = N

    # Ensure only one of spans, kernel is provided, and build the kernel window if needed
    assert (spans is None) or (kernel is None), "must specify only one of 'spans' or 'kernel'"
    if spans is not None:
        kernel = daniell_window_convolve(np.floor_divide(np.r_[spans], 2))

    # Detrend or demean the series
    if detrend:
        t = np.arange(N) - (N - 1)/2
        sumt2 = N * (N**2 - 1)/12
        x -= (np.repeat(np.expand_dims(np.mean(x, axis=0), 0), N, axis=0) + np.outer(np.sum(x.T * t, axis=1), t/sumt2).T)
    elif demean:
        x -= np.mean(x, axis=0)

    # Compute taper and taper adjustment variables
    x = spec_taper(x, taper)
    u2 = (1 - (5/8) * taper * 2)
    u4 = (1 - (93/128) * taper * 2)

    # Pad the series with copies of the same shape, but filled with zeroes
    if pad > 0:
        x = np.r_[x, np.zeros((pad * x.shape[0], x.shape[1]))]
        N = x.shape[0]

    # Further pad the series to accelerate FFT computation
    if fast:
        newN = fft.next_fast_len(N, True)
        x = np.r_[x, np.zeros((newN - N, x.shape[1]))]
        N = newN

    # Compute the Fourier frequencies (R's spec.pgram convention style)
    Nspec = int(np.floor(N/2))
    freq = (np.arange(Nspec) + 1) * xfreq / N

    # Translations to keep same row / column convention as stats::mvfft
    xfft = fft.fft(x.T).T

    # Compute the periodogram for each i, j
    pgram = np.empty((N, nser, nser), dtype='complex')
    for i in range(nser):
        for j in range(nser):
            pgram[:, i, j] = xfft[:, i] * np.conj(xfft[:, j]) / (N0 * xfreq)
            pgram[0, i, j] = 0.5 * (pgram[1, i, j] + pgram[-1, i, j])

    if kernel is None:
        # Values pre-adjustment
        df = 2
        bandwidth = np.sqrt(1 / 12)
    else:


# alffmap - 23 lines
def alffmap( x, flo=0.01, fhi=0.1, tr=1, detrend = True ):
    """
    Amplitude of Low Frequency Fluctuations (ALFF; Zang et al., 2007) and
    fractional Amplitude of Low Frequency Fluctuations (f/ALFF; Zou et al., 2008)
    are related measures that quantify the amplitude of low frequency
    oscillations (LFOs).  This function outputs ALFF and fALFF for the input.
    same function in ANTsR.

    x input vector for the time series of interest
    flo low frequency, typically 0.01
    fhi high frequency, typically 0.1
    tr the period associated with the vector x (inverse of frequency)
    detrend detrend the input time series

    return vector is output showing ALFF and fALFF values
    """
    temp = spec_pgram( x, xfreq=1.0/tr, demean=False, detrend=detrend, taper=0, fast=True, plot=False )
    fselect = np.logical_and( temp['freq'] >= flo, temp['freq'] <= fhi )
    denom = (temp['spec']).sum()
    numer = (temp['spec'][fselect]).sum()
    return {  'alff':numer, 'falff': numer/denom }



