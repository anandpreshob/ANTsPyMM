"""
Registration functions for ANTsPyMM
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

# dti_reg
def dti_reg(
    image,
    avg_b0,
    avg_dwi,
    bvals=None,
    bvecs=None,
    b0_idx=None,
    type_of_transform="antsRegistrationSyNRepro[r]",
    total_sigma=3.0,
    fdOffset=2.0,
    mask_csf=False,
    brain_mask_eroded=None,
    output_directory=None,
    verbose=False, **kwargs
):
    """
    Correct time-series data for motion - with optional deformation.

    Arguments
    ---------
        image: antsImage, usually ND where D=4.

        avg_b0: Fixed image b0 image

        avg_dwi: Fixed dwi same space as b0 image

        bvals: bvalues (file or array)

        bvecs: bvecs (file or array)

        b0_idx: indices of b0

        type_of_transform : string
            A linear or non-linear registration type. Mutual information metric and rigid transformation by default.
            See ants registration for details.

        fdOffset: offset value to use in framewise displacement calculation

        mask_csf: boolean

        brain_mask_eroded: optional mask that will trigger mixed interpolation

        output_directory : string
            output will be placed in this directory plus a numeric extension.

        verbose: boolean

        kwargs: keyword args
            extra arguments - these extra arguments will control the details of registration that is performed. see ants registration for more.

    Returns
    -------
    dict containing follow key/value pairs:
        `motion_corrected`: Moving image warped to space of fixed image.
        `motion_parameters`: transforms for each image in the time series.
        `FD`: Framewise displacement generalized for arbitrary transformations.

    Notes
    -----
    Control extra arguments via kwargs. see ants.registration for details.

    Example
    -------
    >>> import ants
    """

    idim = image.dimension
    ishape = image.shape
    nTimePoints = ishape[idim - 1]
    FD = np.zeros(nTimePoints)
    if bvals is not None and bvecs is not None:
        if isinstance(bvecs, str):
            bvals, bvecs = read_bvals_bvecs( bvals , bvecs  )
        else: # assume we already read them
            bvals = bvals.copy()
            bvecs = bvecs.copy()
    if type_of_transform is None:
        return {
            "motion_corrected": image,
            "motion_parameters": None,
            "FD": FD,
            'bvals':bvals,
            'bvecs':bvecs
        }

    from scipy.linalg import inv, polar
    from dipy.core.gradients import reorient_bvecs

    remove_it=False
    if output_directory is None:
        remove_it=True
        output_directory = tempfile.mkdtemp()
    output_directory_w = output_directory + "/dti_reg/"
    os.makedirs(output_directory_w,exist_ok=True)
    ofnG = tempfile.NamedTemporaryFile(delete=False,suffix='global_deformation',dir=output_directory_w).name
    ofnL = tempfile.NamedTemporaryFile(delete=False,suffix='local_deformation',dir=output_directory_w).name
    if verbose:
        print(output_directory_w)
        print(ofnG)
        print(ofnL)
        print("remove_it " + str( remove_it ) )

    if b0_idx is None:
        # b0_idx = segment_timeseries_by_meanvalue( image )['highermeans']
        b0_idx = segment_timeseries_by_bvalue( bvals )['lowbvals']

    # first get a local deformation from slice to local avg space
    # then get a global deformation from avg to ref space
    ab0, adw = get_average_dwi_b0( image )
    # mask is used to roughly locate middle of brain
    mask = ants.threshold_image( ants.iMath(adw,'Normalize'), 0.1, 1.0 )
    if brain_mask_eroded is None:
        brain_mask_eroded = mask * 0 + 1
    motion_parameters = list()
    motion_corrected = list()
    centerOfMass = mask.get_center_of_mass()
    npts = pow(2, idim - 1)
    pointOffsets = np.zeros((npts, idim - 1))
    myrad = np.ones(idim - 1).astype(int).tolist()
    mask1vals = np.zeros(int(mask.sum()))
    mask1vals[round(len(mask1vals) / 2)] = 1
    mask1 = ants.make_image(mask, mask1vals)
    myoffsets = ants.get_neighborhood_in_mask(
        mask1, mask1, radius=myrad, spatial_info=True
    )["offsets"]
    mycols = list("xy")
    if idim - 1 == 3:
        mycols = list("xyz")
    useinds = list()
    for k in range(myoffsets.shape[0]):
        if abs(myoffsets[k, :]).sum() == (idim - 2):
            useinds.append(k)
        myoffsets[k, :] = myoffsets[k, :] * fdOffset / 2.0 + centerOfMass
    fdpts = pd.DataFrame(data=myoffsets[useinds, :], columns=mycols)


    if verbose:
        print("begin global distortion correction")
    # initrig = tra_initializer(avg_b0, ab0, max_rotation=60, transform=['rigid'], verbose=verbose)
    if mask_csf:
        bcsf = ants.threshold_image( avg_b0,"Otsu",2).threshold_image(1,1).morphology("open",1).iMath("GetLargestComponent")
    else:
        bcsf = ab0 * 0 + 1

    initrig = ants.registration( avg_b0, ab0,'antsRegistrationSyNRepro[r]',outprefix=ofnG)
    deftx = ants.registration( avg_dwi, adw, 'SyNOnly',
        syn_metric='CC', syn_sampling=2,
        reg_iterations=[50,50,20],
        multivariate_extras=[ [ "CC", avg_b0, ab0, 1, 2 ]],
        initial_transform=initrig['fwdtransforms'][0],
        outprefix=ofnG
        )['fwdtransforms']
    if verbose:
        print("end global distortion correction")

    if verbose:
        print("Progress:")
    counter = round( nTimePoints / 10 ) + 1
    for k in range(nTimePoints):
        if verbose and nTimePoints > 0 and ( ( k % counter ) ==  0 ) or ( k == (nTimePoints-1) ):
            myperc = round( k / nTimePoints * 100)
            print(myperc, end="%.", flush=True)
        if k in b0_idx:
            fixed=ants.image_clone( ab0 )
        else:
            fixed=ants.image_clone( adw )
        temp = ants.slice_image(image, axis=idim - 1, idx=k)
        temp = ants.iMath(temp, "Normalize")
        txprefix = ofnL+str(k).zfill(4)+"rig_"
        txprefix2 = ofnL+str(k % 2).zfill(4)+"def_"
        if temp.numpy().var() > 0:
            myrig = ants.registration(
                    fixed, temp,
                    type_of_transform='antsRegistrationSyNRepro[r]',
                    outprefix=txprefix,
                    **kwargs
                )
            if type_of_transform == 'SyN':
                myreg = ants.registration(
                    fixed, temp,
                    type_of_transform='SyNOnly',
                    total_sigma=total_sigma, grad_step=0.1,
                    initial_transform=myrig['fwdtransforms'][0],
                    outprefix=txprefix2,
                    **kwargs
                )
            else:
                myreg = myrig
            fdptsTxI = ants.apply_transforms_to_points(
                idim - 1, fdpts, myrig["fwdtransforms"]
            )
            if k > 0 and motion_parameters[k - 1] != "NA":
                fdptsTxIminus1 = ants.apply_transforms_to_points(
                    idim - 1, fdpts, motion_parameters[k - 1]
                )
            else:
                fdptsTxIminus1 = fdptsTxI
            # take the absolute value, then the mean across columns, then the sum
            FD[k] = (fdptsTxIminus1 - fdptsTxI).abs().mean().sum()
            motion_parameters.append(myreg["fwdtransforms"])
        else:
            motion_parameters.append("NA")

        temp = ants.slice_image(image, axis=idim - 1, idx=k)
        if k in b0_idx:
            fixed=ants.image_clone( ab0 )
        else:
            fixed=ants.image_clone( adw )
        if temp.numpy().var() > 0:
            motion_parameters[k]=deftx+motion_parameters[k]
            img1w = apply_transforms_mixed_interpolation( avg_dwi,
                ants.slice_image(image, axis=idim - 1, idx=k),
                motion_parameters[k], mask=brain_mask_eroded )
            motion_corrected.append(img1w)
        else:
            motion_corrected.append(fixed)

    if verbose:
        print("Reorient bvecs")
    if bvecs is not None:
        #    direction = target->GetDirection().GetTranspose() * img_mov->GetDirection().GetVnlMatrix();
        rebase = np.dot( np.transpose( avg_b0.direction  ), ab0.direction )
        bvecs = bvec_reorientation( motion_parameters, bvecs, rebase )

    if remove_it:
        import shutil
        shutil.rmtree(output_directory, ignore_errors=True )

    if verbose:
        print("Done")
    d4siz = list(avg_b0.shape)
    d4siz.append( 2 )
    spc = list(ants.get_spacing( avg_b0 ))
    spc.append( 1.0 )
    mydir = ants.get_direction( avg_b0 )
    mydir4d = ants.get_direction( image )
    mydir4d[0:3,0:3]=mydir
    myorg = list(ants.get_origin( avg_b0 ))
    myorg.append( 0.0 )
    avg_b0_4d = ants.make_image(d4siz,0,spacing=spc,origin=myorg,direction=mydir4d)
    return {
        "motion_corrected": ants.list_to_ndimage(avg_b0_4d, motion_corrected),
        "motion_parameters": motion_parameters,
        "FD": FD,
        'bvals':bvals,
        'bvecs':bvecs
    }




# timeseries_reg
def timeseries_reg(
    image,
    avg_b0,
    type_of_transform='antsRegistrationSyNRepro[r]',
    total_sigma=1.0,
    fdOffset=2.0,
    trim = 0,
    output_directory=None,
    return_numpy_motion_parameters=False,
    verbose=False, **kwargs
):
    """
    Correct time-series data for motion.

    Arguments
    ---------
    image: antsImage, usually ND where D=4.

    avg_b0: Fixed image b0 image

    type_of_transform : string
            A linear or non-linear registration type. Mutual information metric and rigid transformation by default.
            See ants registration for details.

    fdOffset: offset value to use in framewise displacement calculation

    trim : integer - trim this many images off the front of the time series

    output_directory : string
            output will be placed in this directory plus a numeric extension.

    return_numpy_motion_parameters : boolean

    verbose: boolean

    kwargs: keyword args
            extra arguments - these extra arguments will control the details of registration that is performed. see ants registration for more.

    Returns
    -------
    dict containing follow key/value pairs:
        `motion_corrected`: Moving image warped to space of fixed image.
        `motion_parameters`: transforms for each image in the time series.
        `FD`: Framewise displacement generalized for arbitrary transformations.

    Notes
    -----
    Control extra arguments via kwargs. see ants.registration for details.

    Example
    -------
    >>> import ants
    """
    idim = image.dimension
    ishape = image.shape
    nTimePoints = ishape[idim - 1]
    FD = np.zeros(nTimePoints)
    if type_of_transform is None:
        return {
            "motion_corrected": image,
            "motion_parameters": None,
            "FD": FD
        }

    remove_it=False
    if output_directory is None:
        remove_it=True
        output_directory = tempfile.mkdtemp()
    output_directory_w = output_directory + "/ts_reg/"
    os.makedirs(output_directory_w,exist_ok=True)
    ofnG = tempfile.NamedTemporaryFile(delete=False,suffix='global_deformation',dir=output_directory_w).name
    ofnL = tempfile.NamedTemporaryFile(delete=False,suffix='local_deformation',dir=output_directory_w).name
    if verbose:
        print('bold motcorr with ' + type_of_transform)
        print(output_directory_w)
        print(ofnG)
        print(ofnL)
        print("remove_it " + str( remove_it ) )

    # get a local deformation from slice to local avg space
    motion_parameters = list()
    motion_corrected = list()
    mask = ants.get_mask( avg_b0 )
    centerOfMass = mask.get_center_of_mass()
    npts = pow(2, idim - 1)
    pointOffsets = np.zeros((npts, idim - 1))
    myrad = np.ones(idim - 1).astype(int).tolist()
    mask1vals = np.zeros(int(mask.sum()))
    mask1vals[round(len(mask1vals) / 2)] = 1
    mask1 = ants.make_image(mask, mask1vals)
    myoffsets = ants.get_neighborhood_in_mask(
        mask1, mask1, radius=myrad, spatial_info=True
    )["offsets"]
    mycols = list("xy")
    if idim - 1 == 3:
        mycols = list("xyz")
    useinds = list()
    for k in range(myoffsets.shape[0]):
        if abs(myoffsets[k, :]).sum() == (idim - 2):
            useinds.append(k)
        myoffsets[k, :] = myoffsets[k, :] * fdOffset / 2.0 + centerOfMass
    fdpts = pd.DataFrame(data=myoffsets[useinds, :], columns=mycols)
    if verbose:
        print("Progress:")
    counter = round( nTimePoints / 10 ) + 1
    for k in range( nTimePoints):
        if verbose and ( ( k % counter ) ==  0 ) or ( k == (nTimePoints-1) ):
            myperc = round( k / nTimePoints * 100)
            print(myperc, end="%.", flush=True)
        temp = ants.slice_image(image, axis=idim - 1, idx=k)
        temp = ants.iMath(temp, "Normalize")
        txprefix = ofnL+str(k % 2).zfill(4)+"_"
        if temp.numpy().var() > 0:
            myrig = ants.registration(
                    avg_b0, temp,
                    type_of_transform='antsRegistrationSyNRepro[r]',
                    outprefix=txprefix
                )
            if type_of_transform == 'SyN':
                myreg = ants.registration(
                    avg_b0, temp,
                    type_of_transform='SyNOnly',
                    total_sigma=total_sigma,
                    initial_transform=myrig['fwdtransforms'][0],
                    outprefix=txprefix,
                    **kwargs
                )
            else:
                myreg = myrig
            fdptsTxI = ants.apply_transforms_to_points(
                idim - 1, fdpts, myrig["fwdtransforms"]
            )
            if k > 0 and motion_parameters[k - 1] != "NA":
                fdptsTxIminus1 = ants.apply_transforms_to_points(
                    idim - 1, fdpts, motion_parameters[k - 1]
                )
            else:
                fdptsTxIminus1 = fdptsTxI
            # take the absolute value, then the mean across columns, then the sum
            FD[k] = (fdptsTxIminus1 - fdptsTxI).abs().mean().sum()
            motion_parameters.append(myreg["fwdtransforms"])
        else:
            motion_parameters.append("NA")

        temp = ants.slice_image(image, axis=idim - 1, idx=k)
        if temp.numpy().var() > 0:
            img1w = ants.apply_transforms( avg_b0,
                temp,
                motion_parameters[k] )
            motion_corrected.append(img1w)
        else:
            motion_corrected.append(avg_b0)

    motion_parameters = motion_parameters[trim:len(motion_parameters)]
    if return_numpy_motion_parameters:
        motion_parameters = read_ants_transforms_to_numpy( motion_parameters )

    if remove_it:
        import shutil
        shutil.rmtree(output_directory, ignore_errors=True )

    if verbose:
        print("Done")
    d4siz = list(avg_b0.shape)
    d4siz.append( 2 )
    spc = list(ants.get_spacing( avg_b0 ))
    spc.append( ants.get_spacing(image)[3] )
    mydir = ants.get_direction( avg_b0 )
    mydir4d = ants.get_direction( image )
    mydir4d[0:3,0:3]=mydir
    myorg = list(ants.get_origin( avg_b0 ))
    myorg.append( 0.0 )
    avg_b0_4d = ants.make_image(d4siz,0,spacing=spc,origin=myorg,direction=mydir4d)
    return {
        "motion_corrected": ants.list_to_ndimage(avg_b0_4d, motion_corrected[trim:len(motion_corrected)]),
        "motion_parameters": motion_parameters,
        "FD": FD[trim:len(FD)]
    }




# mc_reg
def mc_reg(
    image,
    fixed=None,
    type_of_transform="antsRegistrationSyNRepro[r]",
    mask=None,
    total_sigma=3.0,
    fdOffset=2.0,
    output_directory=None,
    verbose=False, **kwargs
):
    """
    Correct time-series data for motion - with deformation.

    Arguments
    ---------
        image: antsImage, usually ND where D=4.

        fixed: Fixed image to register all timepoints to.  If not provided,
            mean image is used.

        type_of_transform : string
            A linear or non-linear registration type. Mutual information metric and rigid transformation by default.
            See ants registration for details.

        fdOffset: offset value to use in framewise displacement calculation

        output_directory : string
            output will be named with this prefix plus a numeric extension.

        verbose: boolean

        kwargs: keyword args
            extra arguments - these extra arguments will control the details of registration that is performed. see ants registration for more.

    Returns
    -------
    dict containing follow key/value pairs:
        `motion_corrected`: Moving image warped to space of fixed image.
        `motion_parameters`: transforms for each image in the time series.
        `FD`: Framewise displacement generalized for arbitrary transformations.

    Notes
    -----
    Control extra arguments via kwargs. see ants.registration for details.

    Example
    -------
    >>> import ants
    >>> fi = ants.image_read(ants.get_ants_data('ch2'))
    >>> mytx = ants.motion_correction( fi )
    """
    remove_it=False
    if output_directory is None:
        remove_it=True
        output_directory = tempfile.mkdtemp()
    output_directory_w = output_directory + "/mc_reg/"
    os.makedirs(output_directory_w,exist_ok=True)
    ofnG = tempfile.NamedTemporaryFile(delete=False,suffix='global_deformation',dir=output_directory_w).name
    ofnL = tempfile.NamedTemporaryFile(delete=False,suffix='local_deformation',dir=output_directory_w).name
    if verbose:
        print(output_directory_w)
        print(ofnG)
        print(ofnL)

    idim = image.dimension
    ishape = image.shape
    nTimePoints = ishape[idim - 1]
    if fixed is None:
        fixed = ants.get_average_of_timeseries( image )
    if mask is None:
        mask = ants.get_mask(fixed)
    FD = np.zeros(nTimePoints)
    motion_parameters = list()
    motion_corrected = list()
    centerOfMass = mask.get_center_of_mass()
    npts = pow(2, idim - 1)
    pointOffsets = np.zeros((npts, idim - 1))
    myrad = np.ones(idim - 1).astype(int).tolist()
    mask1vals = np.zeros(int(mask.sum()))
    mask1vals[round(len(mask1vals) / 2)] = 1
    mask1 = ants.make_image(mask, mask1vals)
    myoffsets = ants.get_neighborhood_in_mask(
        mask1, mask1, radius=myrad, spatial_info=True
    )["offsets"]
    mycols = list("xy")
    if idim - 1 == 3:
        mycols = list("xyz")
    useinds = list()
    for k in range(myoffsets.shape[0]):
        if abs(myoffsets[k, :]).sum() == (idim - 2):
            useinds.append(k)
        myoffsets[k, :] = myoffsets[k, :] * fdOffset / 2.0 + centerOfMass
    fdpts = pd.DataFrame(data=myoffsets[useinds, :], columns=mycols)
    if verbose:
        print("Progress:")
    counter = 0
    for k in range(nTimePoints):
        mycount = round(k / nTimePoints * 100)
        if verbose and mycount == counter:
            counter = counter + 10
            print(mycount, end="%.", flush=True)
        temp = ants.slice_image(image, axis=idim - 1, idx=k)
        temp = ants.iMath(temp, "Normalize")
        if temp.numpy().var() > 0:
            myrig = ants.registration(
                    fixed, temp,
                    type_of_transform='antsRegistrationSyNRepro[r]',
                    outprefix=ofnL+str(k).zfill(4)+"_",
                    **kwargs
                )
            if type_of_transform == 'SyN':
                myreg = ants.registration(
                    fixed, temp,
                    type_of_transform='SyNOnly',
                    total_sigma=total_sigma,
                    initial_transform=myrig['fwdtransforms'][0],
                    outprefix=ofnL+str(k).zfill(4)+"_",
                    **kwargs
                )
            else:
                myreg = myrig
            fdptsTxI = ants.apply_transforms_to_points(
                idim - 1, fdpts, myreg["fwdtransforms"]
            )
            if k > 0 and motion_parameters[k - 1] != "NA":
                fdptsTxIminus1 = ants.apply_transforms_to_points(
                    idim - 1, fdpts, motion_parameters[k - 1]
                )
            else:
                fdptsTxIminus1 = fdptsTxI
            # take the absolute value, then the mean across columns, then the sum
            FD[k] = (fdptsTxIminus1 - fdptsTxI).abs().mean().sum()
            motion_parameters.append(myreg["fwdtransforms"])
            img1w = ants.apply_transforms( fixed,
                ants.slice_image(image, axis=idim - 1, idx=k),
                myreg["fwdtransforms"] )
            motion_corrected.append(img1w)
        else:
            motion_parameters.append("NA")
            motion_corrected.append(temp)

    if remove_it:
        import shutil
        shutil.rmtree(output_directory, ignore_errors=True )

    if verbose:
        print("Done")
    return {
        "motion_corrected": ants.list_to_ndimage(image, motion_corrected),
        "motion_parameters": motion_parameters,
        "FD": FD,
    }



# transform_and_reorient_dti
def transform_and_reorient_dti( fixed, moving_dti, composite_transform, verbose=False, **kwargs):
    """
    Applies a transformation to a DTI image using an ANTs composite transform,
    including local tensor reorientation via the Finite Strain method.

    This function expects:
    - Input `moving_dti` to be a 6-component ANTsImage (upper triangular format).
    - `composite_transform` to point to an ANTs-readable transform file,
      which maps points from `fixed` space to `moving` space.

    Args:
        fixed (ants.ANTsImage): The reference space image (defines the output grid).
        moving_dti (ants.ANTsImage): The input DTI (6-component), to be transformed.
        composite_transform (str): File path to an ANTs transform
                                   (e.g., from `ants.read_transform` or a written composite transform).
        verbose (bool): Whether to print verbose output during execution.
        **kwargs: Additional keyword arguments passed to `ants.apply_transforms`.

    Returns:
        ants.ANTsImage: The transformed and reoriented DTI image in the `fixed` space,
                        in 6-component upper triangular format.
    """
    if moving_dti.dimension != 3:
        raise ValueError('moving_dti must be 3-dimensional.')
    if moving_dti.components != 6:
        raise ValueError('moving_dti must have 6 components (upper triangular format).')

    if verbose:
        print("1. Spatially transforming DTI scalar components from moving to fixed space...")

    # ants.apply_transforms resamples the *values* of each DTI component from 'moving_dti'
    # onto the grid of 'fixed'.
    # The output 'dtiw' will have the same spatial metadata (spacing, origin, direction) as 'fixed'.
    # However, the tensor values contained within it are still oriented as they were in
    # 'moving_dti's original image space, not 'fixed' image space, and certainly not yet reoriented
    # by the local deformation.
    dtsplit = moving_dti.split_channels()
    dtiw_channels = []
    for k in range(len(dtsplit)):
        dtiw_channels.append( ants.apply_transforms( fixed, dtsplit[k], composite_transform, **kwargs ) )
    dtiw = ants.merge_channels(dtiw_channels)
    
    if verbose:
        print(f"   DTI scalar components resampled to fixed grid. Result shape: {dtiw.shape}")
        print("2. Computing local rotation field from composite transform...")
    
    # Read the composite transform as an image (assumed to be a displacement field).
    # The 'deformation_gradient_optimized' function is assumed to be 100% correct,
    # meaning it returns the appropriate local rotation matrix field (R_moving_to_fixed)
    # in (spatial_dims..., 3, 3 ) format when called with these flags.
    wtx = ants.image_read(composite_transform)
    R_moving_to_fixed_forward = deformation_gradient_optimized(
        wtx,
        to_rotation=False,      # This means the *deformation gradient* F=I+J is computed first.
        to_inverse_rotation=True # This requests the inverse of the rotation part of F.
    )

    if verbose:
        print(f"   Local reorientation matrices (R_moving_to_fixed_forward) computed. Shape: {R_moving_to_fixed_forward.shape}")
        print("3. Converting 6-component DTI to full 3x3 tensors for vectorized reorientation...")
    
    # Convert `dtiw` (resampled, but still in moving-image-space orientation)
    # from 6-components to full 3x3 tensor representation.
    # dtiw2tensor_np will have shape (spatial_dims..., 3, 3).
    dtiw2tensor_np = triangular_to_tensor(dtiw)
    
    if verbose:
        print("4. Applying vectorized tensor reorientation (Finite Strain Method)...")
    
    # --- Vectorized Tensor Reorientation ---
    # This replaces the entire `for i in it:` loop and its contents with efficient NumPy operations.

    # Step 4.1: Rebase tensors from `moving_dti.direction` coordinate system to World Coordinates.
    # D_world_moving_orient = moving_dti.direction @ D_moving_image_frame @ moving_dti.direction.T
    # This transforms the tensor's components from being relative to `moving_dti`'s image axes
    # (where they are currently defined) into absolute World (physical) coordinates.
    D_world_moving_orient = np.einsum(
        'ab, ...bc, cd -> ...ad',
        moving_dti.direction,            # 3x3 matrix (moving_image_axes -> world_axes)
        dtiw2tensor_np,                  # (spatial_dims..., 3, 3)
        moving_dti.direction.T           # 3x3 matrix (world_axes -> moving_image_axes) - inverse of moving_dti.direction
    )

    # Step 4.2: Apply local rotation in World Coordinates (Finite Strain Reorientation).
    # D_reoriented_world = R_moving_to_fixed_forward @ D_world_moving_orient @ (R_moving_to_fixed_forward).T
    # This is the core reorientation step, transforming the tensor's orientation from
    # the original `moving` space to the new `fixed` space, all within world coordinates.
    D_world_fixed_orient = np.einsum(
        '...ab, ...bc, ...cd -> ...ad',
        R_moving_to_fixed_forward,      # (spatial_dims..., 3, 3) - local rotation
        D_world_moving_orient,          # (spatial_dims..., 3, 3) - tensor in world space, moving_orient
        np.swapaxes(R_moving_to_fixed_forward, -1, -2) # (spatial_dims..., 3, 3) - transpose of local rotation
    )

    # Step 4.3: Rebase reoriented tensors from World Coordinates to `fixed.direction` coordinate system.
    # D_final_fixed_image_frame = (fixed.direction).T @ D_world_fixed_orient @ fixed.direction
    # This transforms the tensor's components from absolute World (physical) coordinates
    # back into `fixed.direction`'s image coordinate system.
    final_dti_tensors_numpy = np.einsum(
        'ba, ...bc, cd -> ...ad',
        fixed.direction,                # Using `fixed.direction` here, but 'ba' indices specify to use its transpose.
        D_world_fixed_orient,           # (spatial_dims..., 3, 3)
        fixed.direction                 # 3x3 matrix (world_axes -> fixed_image_axes)
    )

    if verbose:
        print("   Vectorized tensor reorientation complete.")

    if verbose:
        print("5. Converting reoriented full tensors back to 6-component ANTsImage...")
    
    # Convert the final (spatial_dims..., 3, 3) NumPy array of tensors back into a
    # 6-component ANTsImage with the correct spatial metadata from `fixed`.
    final_dti_image = dti_numpy_to_image(fixed, final_dti_tensors_numpy)
    
    if verbose:
        print(f"Done. Final reoriented DTI image in fixed space generated. Shape: {final_dti_image.shape}")

    return final_dti_image



# apply_transforms_mixed_interpolation
def apply_transforms_mixed_interpolation(
    fixed,
    moving,
    transformlist,
    interpolator="linear",
    imagetype=0,
    whichtoinvert=None,
    mask=None,
    **kwargs
):
    """
    Apply ANTs transforms with mixed interpolation:
    - Linear interpolation inside `mask`
    - Nearest neighbor outside `mask`

    Parameters
    ----------
    fixed : ANTsImage
        Fixed/reference image to define spatial domain.

    moving : ANTsImage
        Moving image to be transformed.

    transformlist : list of str
        List of filenames for transforms.

    interpolator : str, optional
        Interpolator used inside the mask. Default is "linear".

    imagetype : int
        Image type used by ANTs (0 = scalar, 1 = vector, etc.)

    whichtoinvert : list of bool, optional
        List of booleans indicating which transforms to invert.

    mask : ANTsImage
        Binary mask image indicating where to apply `interpolator` (e.g., "linear").
        Outside the mask, nearest neighbor is used.

    kwargs : dict
        Additional arguments passed to `ants.apply_transforms`.

    Returns
    -------
    ANTsImage
        Interpolated image using mixed interpolation, added across masked regions.
    """
    if mask is None:
        raise ValueError("A binary `mask` image must be provided.")

    # Apply linear interpolation inside the mask
    interp_linear = ants.apply_transforms(
        fixed=fixed,
        moving=moving,
        transformlist=transformlist,
        interpolator=interpolator,
        imagetype=imagetype,
        whichtoinvert=whichtoinvert,
        **kwargs
    )

    # Apply nearest-neighbor interpolation everywhere
    interp_nn = ants.apply_transforms(
        fixed=fixed,
        moving=moving,
        transformlist=transformlist,
        interpolator="nearestNeighbor",
        imagetype=imagetype,
        whichtoinvert=whichtoinvert,
        **kwargs
    )

    # Combine: linear * mask + nn * (1 - mask)
    mixed_result = (interp_linear * mask) + (interp_nn * (1 - mask))

    return mixed_result



