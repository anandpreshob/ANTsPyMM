"""
Signal_Processing functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

# Standard library imports
import os
import numpy as np
import pandas as pd

# Conditional imports
try:
    import ants
except ImportError:
    ants = None

# daniell_window_convolve
    def daniell_window_convolve(v):
        """ Convolved version of multiple modified Daniell kernel windows.

        Parameter v should be an iterable of m values.
        """

        if len(v) == 0:
            return np.r_[1]

        if len(v) == 1:
            return daniell_window_modified(v[0])

        return signal.convolve(daniell_window_modified(v[0]), daniell_window_convolve(v[1:]))

    # Ensure we can store non-integers in x, and that it is a numpy object
    x = np.r_[x].astype('float64')
    original_shape = x.shape

    # Ensure correct dimensions
    assert len(original_shape) <= 2, "'x' must have at most 2 dimensions"
    while len(x.shape) < 2:
        x = np.expand_dims(x, axis=1)

    N, nser = x.shape


# conv_circular
        def conv_circular(signal, kernel):
            """
            Performs 1D circular convolution, in the same style as R::kernapply,
            assuming the kernel window is centered at 0.
            """
            pad = len(signal) - len(kernel)
            half_window = int((len(kernel) + 1) / 2)
            indexes = range(-half_window, len(signal) - half_window)
            orig_conv = np.real(fft.ifft(fft.fft(signal) * fft.fft(np.r_[np.zeros(pad), kernel])))
            return orig_conv.take(indexes, mode='wrap')

        # Convolve pgram with kernel with circular conv
        for i in range(nser):
            for j in range(nser):
                pgram[:, i, j] = conv_circular(pgram[:, i, j], kernel)

        df = 2 / np.sum(kernel**2)
        m = (len(kernel) - 1)/2
        k = np.arange(-m, m+1)
        bandwidth = np.sqrt(np.sum((1/12 + k**2) * kernel))

    df = df/(u4/u2**2)*(N0/N)
    bandwidth = bandwidth * xfreq/N

    # Remove padded results
    pgram = pgram[1:(Nspec+1), :, :]

    spec = np.empty((Nspec, nser))
    for i in range(nser):
        spec[:, i] = np.real(pgram[:, i, i])

    if nser == 1:
        coh = None
        phase = None
    else:
        coh = np.empty((Nspec, int(nser * (nser - 1)/2)))
        phase = np.empty((Nspec, int(nser * (nser - 1)/2)))
        for i in range(nser):
            for j in range(i+1, nser):
                index = int(i + j*(j-1)/2)
                coh[:, index] = np.abs(pgram[:, i, j])**2 / (spec[:, i] * spec[:, j])
                phase[:, index] = np.angle(pgram[:, i, j])

    spec = spec / u2
    spec = spec.squeeze()

    results = {
        'freq': freq,
        'spec': spec,
        'coh': coh,
        'phase': phase,
        'kernel': kernel,
        'df': df,
        'bandwidth': bandwidth,
        'n.used': N,
        'orig.n': N0,
        'taper': taper,
        'pad': pad,
        'detrend': detrend,
        'demean': demean,
        'method': 'Raw Periodogram' if kernel is None else 'Smoothed Periodogram'
    }

    if plot:
        plot_spec(results, coverage=0.95, **kwargs)

    return results



