"""
Dwi functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# distortion_correct_bvecs - 33 lines
def distortion_correct_bvecs(bvecs, def_grad, A_img, A_ref):
    """
    Vectorized computation of voxel-wise distortion corrected b-vectors.

    Parameters
    ----------
    bvecs : ndarray (N, 3)
    def_grad : ndarray (X, Y, Z, 3, 3) containing rotations derived from the deformation gradient
    A_img : ndarray (3, 3) direction matrix of the fixed image (target undistorted space)
    A_ref : ndarray (3, 3) direction matrix of the moving image (being corrected)

    Returns
    -------
    bvecs_5d : ndarray (X, Y, Z, N, 3)
    """
    X, Y, Z = def_grad.shape[:3]
    N = bvecs.shape[0]
    # Combined rotation: R_voxel = A_ref.T @ A_img @ def_grad
    A = A_ref.T @ A_img
    R_voxel = np.einsum('ij,xyzjk->xyzik', A, def_grad)  # (X, Y, Z, 3, 3)
    # Apply R_voxel.T @ bvecs
    # First, reshape R_voxel: (X*Y*Z, 3, 3)
    R_voxel_reshaped = R_voxel.reshape(-1, 3, 3)
    # Rotate all bvecs for each voxel
    # Output: (X*Y*Z, N, 3)
    rotated = np.einsum('vij,nj->vni', R_voxel_reshaped, bvecs)
    # Normalize
    norms = np.linalg.norm(rotated, axis=2, keepdims=True)
    rotated /= np.clip(norms, 1e-8, None)
    # Reshape back to (X, Y, Z, N, 3)
    bvecs_5d = rotated.reshape(X, Y, Z, N, 3)
    return bvecs_5d    



# triangular_to_tensor - 36 lines
def triangular_to_tensor( image, upper_triangular=True ):
    """
    convert triangular tensor image to a full tensor form (in numpy)

    image : antsImage holding dti in either upper or lower triangular format 

    upper_triangular: boolean

    Note
    --------
    see get_dti function for more details
    """
    reoind = np.array([0,1,3,2,4,5]) # arrays are faster than lists
    it = np.ndindex( image.shape )
    yyind=2
    xzind=3
    if upper_triangular:
        yyind=3
        xzind=2
    # copy these data into a tensor 
    dtinp = np.zeros(image.shape + (3,3), dtype=float)
    dtix = np.zeros((3,3), dtype=float)
    it = np.ndindex( image.shape )
    dtiut = image.numpy()
    for i in it:
        dtivec = dtiut[i] # in ANTs - we have: [xx,xy,xz,yy,yz,zz]
        dtix[0,0]=dtivec[0]
        dtix[1,1]=dtivec[yyind] # 2 for LT
        dtix[2,2]=dtivec[5] 
        dtix[0,1]=dtix[1,0]=dtivec[1]
        dtix[0,2]=dtix[2,0]=dtivec[xzind] # 3 for LT
        dtix[1,2]=dtix[2,1]=dtivec[4]
        dtinp[i]=dtix
    return dtinp




# trim_dti_mask - 28 lines
def trim_dti_mask( fa, mask, param=4.0 ):
    """
    trim the dti mask to get rid of bright fa rim

    this function erodes the famask by param amount then segments the rim into
    bright and less bright parts.  the bright parts are trimmed from the mask
    and the remaining edges are cleaned up a bit with closing.

    param: closing radius unit is in physical space
    """
    spacing = ants.get_spacing(mask)
    spacing_product = np.prod( spacing )
    spcmin = min( spacing )
    paramVox = int(np.round( param / spcmin ))
    trim_mask = ants.image_clone( mask )
    trim_mask = ants.iMath( trim_mask, "FillHoles" )
    edgemask = trim_mask - ants.iMath( trim_mask, "ME", paramVox )
    maxk=4
    edgemask = ants.threshold_image( fa * edgemask, "Otsu", maxk )
    edgemask = ants.threshold_image( edgemask, maxk-1, maxk )
    trim_mask[edgemask >= 1 ]=0
    trim_mask = ants.iMath(trim_mask,"ME",paramVox-1)
    trim_mask = ants.iMath(trim_mask,'GetLargestComponent')
    trim_mask = ants.iMath(trim_mask,"MD",paramVox-1)
    return trim_mask





# generate_voxelwise_bvecs - 35 lines
def generate_voxelwise_bvecs(global_bvecs, voxel_rotations, transpose=False):
    """
    Generate voxel-wise b-vectors from a global bvec and voxel-wise rotation field.

    Parameters
    ----------
    global_bvecs : ndarray of shape (N, 3)
        Global diffusion gradient directions.
    voxel_rotations : ndarray of shape (X, Y, Z, 3, 3)
        3x3 rotation matrix for each voxel (can come from Jacobian of deformation field).
    transpose : bool, optional
        If True, transpose the rotation matrices before applying them to the b-vectors.


    Returns
    -------
    bvecs_5d : ndarray of shape (X, Y, Z, N, 3)
        Voxel-specific b-vectors.
    """
    X, Y, Z, _, _ = voxel_rotations.shape
    N = global_bvecs.shape[0]
    bvecs_5d = np.zeros((X, Y, Z, N, 3), dtype=np.float32)

    for n in range(N):
        bvec = global_bvecs[n]
        for i in range(X):
            for j in range(Y):
                for k in range(Z):
                    R = voxel_rotations[i, j, k]
                    if transpose:
                        R = R.T  # Use transpose if needed
                    bvecs_5d[i, j, k, n, :] = R @ bvec
    return bvecs_5d




# impute_dwi - 28 lines
def impute_dwi( dwi, threshold = 0.20, imputeb0=False, mask=None, verbose=False ):
    """
    Identify bad volumes in a dwi and impute them fully automatically.

    :param dwi: ANTsImage representing the time series (4D image).
    :param threshold: threshold (0,1) for outlierness (lower means impute more data)
    :param imputeb0: boolean will impute the b0 with dwi if True
    :param mask: restricts to a region of interest
    :param verbose: boolean
    :return: ANTsImage automatically imputed.
    """
    list1 = segment_timeseries_by_meanvalue( dwi )['highermeans']
    if imputeb0:
        dwib = impute_timeseries( dwi, list1 ) # focus on the dwi - not the b0
        looped, list2 = loop_timeseries_censoring( dwib, threshold, mask )
    else:
        looped, list2 = loop_timeseries_censoring( dwi, threshold, mask )
    if verbose:
        print( list1 )
        print( list2 )
    complement = remove_elements_from_list( list2, list1 )
    if verbose:
        print( "Imputing:")
        print( complement )
    if len( complement ) == 0:
        return dwi
    return impute_timeseries( dwi, complement )



# censor_dwi - 31 lines
def censor_dwi( dwi, bval, bvec, threshold = 0.20, imputeb0=False, mask=None, verbose=False ):
    """
    Identify bad volumes in a dwi and impute them fully automatically.

    :param dwi: ANTsImage representing the time series (4D image).
    :param bval: bval array
    :param bvec: bvec array
    :param threshold: threshold (0,1) for outlierness (lower means impute more data)
    :param imputeb0: boolean will impute the b0 with dwi if True
    :param mask: restricts to a region of interest
    :param verbose: boolean
    :return: ANTsImage automatically imputed.
    """
    list1 = segment_timeseries_by_meanvalue( dwi )['highermeans']
    if imputeb0:
        dwib = impute_timeseries( dwi, list1 ) # focus on the dwi - not the b0
        looped, list2 = loop_timeseries_censoring( dwib, threshold, mask, verbose=verbose)
    else:
        looped, list2 = loop_timeseries_censoring( dwi, threshold, mask, verbose=verbose )
    if verbose:
        print( list1 )
        print( list2 )
    complement = remove_elements_from_list( list2, list1 )
    if verbose:
        print( "censoring:")
        print( complement )
    if len( complement ) == 0:
        return dwi, bval, bvec
    return remove_volumes_from_timeseries( dwi, complement ), remove_elements_from_numpy_array( bval, complement ), remove_elements_from_numpy_array( bvec, complement )



