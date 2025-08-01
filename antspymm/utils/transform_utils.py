"""
Transform utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np


def ants_to_nibabel_affine(ants_img):
    """
    Convert an ANTsPy image (in LPS space) to a Nibabel-compatible affine (in RAS space).
    Handles 2D, 3D, 4D input (only spatial dimensions are encoded in the affine).
    
    Returns:
        4x4 np.ndarray affine matrix in RAS space.
    """
    spatial_dim = ants_img.dimension
    spacing = np.array(ants_img.spacing)
    origin = np.array(ants_img.origin)
    direction = np.array(ants_img.direction).reshape((spatial_dim, spatial_dim))
    # Compute rotation-scale matrix
    affine_linear = direction @ np.diag(spacing)
    # Build full 4x4 affine with identity in homogeneous bottom row
    affine = np.eye(4)
    affine[:spatial_dim, :spatial_dim] = affine_linear
    affine[:spatial_dim, 3] = origin
    affine[3, 3]=1
    # Convert LPS -> RAS by flipping x and y
    lps_to_ras = np.diag([-1, -1, 1, 1])
    affine = lps_to_ras @ affine
    return affine