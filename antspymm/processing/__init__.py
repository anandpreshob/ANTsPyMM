"""
Processing modules for ANTsPyMM - refactored from mm.py

This package contains medical image processing functions extracted from the monolithic mm.py file.
All functions maintain their original signatures and behavior.
"""

# Import all processing functions to maintain backward compatibility
from .qc import (
    tsnr,
    dvars,
    mask_snr,
    slice_snr,
    foreground_background_snr,
    quantile_snr
)

from .dti import (
    bvec_reorientation,
    get_dti
)

from .transforms import (
    deformation_gradient_optimized
)

from .segmentation import (
    segment_timeseries_by_bvalue,
    segment_timeseries_by_meanvalue
)

__all__ = [
    # QC functions
    'tsnr',
    'dvars', 
    'mask_snr',
    'slice_snr',
    'foreground_background_snr',
    'quantile_snr',
    # DTI functions
    'bvec_reorientation',
    'get_dti',
    # Transform functions
    'deformation_gradient_optimized',
    # Segmentation functions
    'segment_timeseries_by_bvalue',
    'segment_timeseries_by_meanvalue'
]