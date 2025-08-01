"""
DTI processing functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np

# Import conditionally
try:
    import ants
except ImportError:
    ants = None

try:
    from scipy.linalg import inv, polar
except ImportError:
    inv = None
    polar = None

try:
    from dipy.core.gradients import reorient_bvecs
except ImportError:
    reorient_bvecs = None


def bvec_reorientation( motion_parameters, bvecs, rebase=None ):
    if motion_parameters is None:
        return bvecs
    n = len(motion_parameters)
    if n < 1:
        return bvecs
    
    if inv is None:
        raise ImportError("scipy package is required for bvec_reorientation function")
    if ants is None:
        raise ImportError("ants package is required for bvec_reorientation function")
    
    from scipy.linalg import inv, polar
    from dipy.core.gradients import reorient_bvecs
    dipymoco = np.zeros( [n,3,3] )
    for myidx in range(n):
        if myidx < bvecs.shape[0]:
            dipymoco[myidx,:,:] = np.eye( 3 )
            if motion_parameters[myidx] != 'NA':
                temp = motion_parameters[myidx]
                if len(temp) == 4 :
                    temp1=temp[3] # FIXME should be composite of index 1 and 3
                    temp2=temp[1] # FIXME should be composite of index 1 and 3
                    txparam1 = ants.read_transform(temp1)
                    txparam1 = ants.get_ants_transform_parameters(txparam1)[0:9].reshape( [3,3])
                    txparam2 = ants.read_transform(temp2)
                    txparam2 = ants.get_ants_transform_parameters(txparam2)[0:9].reshape( [3,3])
                    Rinv = inv( np.dot( txparam2, txparam1 ) )
                elif len(temp) == 2 :
                    temp=temp[1] # FIXME should be composite of index 1 and 3
                    txparam = ants.read_transform(temp)
                    txparam = ants.get_ants_transform_parameters(txparam)[0:9].reshape( [3,3])
                    Rinv = inv( txparam )
                elif len(temp) == 3 :
                    temp1=temp[2] # FIXME should be composite of index 1 and 3
                    temp2=temp[1] # FIXME should be composite of index 1 and 3
                    txparam1 = ants.read_transform(temp1)
                    txparam1 = ants.get_ants_transform_parameters(txparam1)[0:9].reshape( [3,3])
                    txparam2 = ants.read_transform(temp2)
                    txparam2 = ants.get_ants_transform_parameters(txparam2)[0:9].reshape( [3,3])
                    Rinv = inv( np.dot( txparam2, txparam1 ) )
                else:
                    temp=temp[0]
                    txparam = ants.read_transform(temp)
                    txparam = ants.get_ants_transform_parameters(txparam)[0:9].reshape( [3,3])
                    Rinv = inv( txparam )
                bvecs[myidx,:] = np.dot( Rinv, bvecs[myidx,:] )
                if rebase is not None:
                    # FIXME - should combine these operations
                    bvecs[myidx,:] = np.dot( rebase, bvecs[myidx,:] )
    return bvecs


def get_dti( reference_image, tensormodel, upper_triangular=True, return_image=False ):
    """
    map the tensor model to its FA and RGB version

    Arguments
    ---------
    reference_image : antsImage
        image that serves as reference space to convert the tensor array into

    tensormodel : ndarray
        dti model from dipy

    upper_triangular : boolean maps a 3x3 matrix to a 6-channel image with
        the upper triangular entries of the matrix ordered as
        XX, XY, XZ, YY, YZ, ZZ

    return_image : boolean return image or numpy array

    Returns
    -------

    Dict containing ndarrays or antsImages with DTI metric(s)

    Example
    -------

    """
    if ants is None:
        raise ImportError("ants package is required for get_dti function")
    
    import dipy.reconst.dti as dti
    from dipy.reconst.dti import fractional_anisotropy, color_fa
    
    evecs = tensormodel.evecs
    FA = fractional_anisotropy(tensormodel.evals)
    # fix nan
    FA[ np.isnan(FA) ] = 0
    FA[ FA > 1.0 ] = 1.0
    FA[ FA < 0.0 ] = 0.0
    evecs[ np.isnan(evecs).any(axis=(3,4)) ] = 0
    FA = np.clip(FA, 0, 1)
    RGB = color_fa(FA, evecs)
    MD = dti.mean_diffusivity(tensormodel.evals)
    AD = dti.axial_diffusivity(tensormodel.evals)
    RD = dti.radial_diffusivity(tensormodel.evals)
    if upper_triangular:
        decf = 1000.0
        outimg = tensormodel.quadratic_form.copy() * decf
        # see https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4110922/
        # these are in "fsl" format such that dxx dxy dxz dyy dyz dzz
        # or :                                   D11 D12 D13 D22 D23 D33
        # from dipy ref: [Dxx, Dxy, Dyy, Dxz, Dyz, Dzz]
        outshape = outimg.shape
        outimgDT = np.zeros( [ outshape[0], outshape[1], outshape[2], 6  ] )
        for myq in range( outshape[3] ):
            if myq == 0:
                outimgDT[:,:,:,0] = outimg[:,:,:,0] # Dxx => D11
            if myq == 1:
                outimgDT[:,:,:,1] = outimg[:,:,:,1] # Dxy => D12
            if myq == 2:
                outimgDT[:,:,:,3] = outimg[:,:,:,2] # Dyy => D22
            if myq == 3:
                outimgDT[:,:,:,2] = outimg[:,:,:,3] # Dxz => D13
            if myq == 4:
                outimgDT[:,:,:,4] = outimg[:,:,:,4] # Dyz => D23
            if myq == 5:
                outimgDT[:,:,:,5] = outimg[:,:,:,5] # Dzz => D33
    else:
        outimgDT = tensormodel.quadratic_form.copy()
    if not return_image:
        outDict = {
            'FA': FA,
            'MD': MD,
            'RD': RD,
            'AD': AD,
            'RGB': RGB,
            'DT' : outimgDT
            }
        return outDict
    else:
        fa = ants.numpy_to_ants( FA, origin=None, spacing=None, direction=None,
                         has_components=False, is_rgb=False, reference=reference_image )
        md = ants.numpy_to_ants( MD, origin=None, spacing=None, direction=None,
                         has_components=False, is_rgb=False, reference=reference_image )
        ad = ants.numpy_to_ants( AD, origin=None, spacing=None, direction=None,
                         has_components=False, is_rgb=False, reference=reference_image )
        rd = ants.numpy_to_ants( RD, origin=None, spacing=None, direction=None,
                         has_components=False, is_rgb=False, reference=reference_image )
        rgb = ants.numpy_to_ants( RGB, origin=None, spacing=None, direction=None,
                         has_components=False, is_rgb=True, reference=reference_image )
        dt = ants.numpy_to_ants( outimgDT, origin=None, spacing=None, direction=None,
                         has_components=True, is_rgb=False, reference=reference_image )
        outDict = {
            'FA': fa,
            'MD': md,
            'RD': rd,
            'AD': ad,
            'RGB': rgb,
            'DT' : dt
            }
        return outDict