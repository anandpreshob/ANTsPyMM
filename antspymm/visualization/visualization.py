"""
Visualization functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# plot_spec - 25 lines
def plot_spec(spec_res, coverage=None, ax=None, title=None):
    import matplotlib.pyplot as plt
    """Convenience plotting method, also includes confidence cross in the same style as R.

    Note that the location of the cross is irrelevant; only width and height matter."""
    f, Pxx = spec_res['freq'], spec_res['spec']

    if coverage is not None:
        ci = spec_ci(spec_res['df'], coverage=coverage)
        conf_x = (max(spec_res['freq']) - spec_res['bandwidth']) + np.r_[-0.5, 0.5] * spec_res['bandwidth']
        conf_y = max(spec_res['spec']) / ci[1]

    if ax is None:
        ax = plt.gca()

    ax.plot(f, Pxx, color='C0')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Log Spectrum')
    ax.set_yscale('log')
    if coverage is not None:
        ax.plot(np.mean(conf_x) * np.r_[1, 1], conf_y * ci, color='red')
        ax.plot(conf_x, np.mean(conf_y) * np.r_[1, 1], color='red')

    ax.set_title(spec_res['method'] if title is None else title)



# brainmap_figure - 30 lines
def brainmap_figure(statistical_df, data_dictionary, output_prefix, brain_image, overlay_cmap='bwr', nslices=21, ncol=7, edge_image_dilation = 0, black_bg=True, axes = [0,1,2], fixed_overlay_range=None, crop=5, verbose=0 ):
    """
    Create figures based on statistical data and an underlying brain image.

    Assumes both ~/.antspyt1w and ~/.antspymm data is available

    Parameters:
    - statistical_df (pandas dataframe): with 2 columns named anat and values
        the anat column should have names that meet *partial matching* criterion 
        with respect to regions that are measured in antspymm.   value will be 
        the value to be displayed.   if two examples of a given region exist in 
        statistical_df, then the largest absolute value will be taken for display.
    - data_dictionary (pandas dataframe): antspymm data dictionary.
    - output_prefix (str): Prefix for the output figure filenames.
    - brain_image (antsImage): the brain image on which results will overlay.
    - overlay_cmap (str): see matplotlib
    - nslices (int): number of slices to show
    - ncol (int): number of columns to show
    - edge_image_dilation (int): integer greater than or equal to zero
    - black_bg (bool): boolean
    - axes (list): integer list typically [0,1,2] sagittal coronal axial
    - fixed_overlay_range (list): scalar pair will try to keep a constant cbar and will truncate the overlay at these min/max values
    - crop (int): crops the image to display by the extent of the overlay; larger values dilate the masks more.
    - verbose (bool): boolean

    Returns:
    an image with values mapped to the associated regions
    """
    import re


