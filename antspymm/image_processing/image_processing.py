"""
Image Processing functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# mc_resample_image_to_target - 11 lines
def mc_resample_image_to_target( x , y, interp_type='linear' ):
    """
    multichannel version of resample_image_to_target
    """
    xx=ants.split_channels( x )
    yy=ants.split_channels( y )[0]
    newl=[]
    for k in range(len(xx)):
        newl.append(  ants.resample_image_to_target( xx[k], yy, interp_type=interp_type ) )
    return ants.merge_channels( newl )



# dti_numpy_to_image - 45 lines
def dti_numpy_to_image( reference_image, tensorarray, upper_triangular=True):
    """
    convert numpy DTI data to antsImage

    reference_image : antsImage defining physical space (3D)

    tensorarray : numpy array X,Y,Z,3,3 shape

    upper_triangular: boolean otherwise use lower triangular coding

    Returns
    -------
    ANTsImage

    Notes
    -----
    DiPy returns lower triangular form but ANTs expects upper triangular.
        Here, we default to the ANTs standard but could generalize in the future 
        because not much here depends on ANTs standards of tensor data.
        ANTs xx,xy,xz,yy,yz,zz
        DiPy Dxx, Dxy, Dyy, Dxz, Dyz, Dzz

    """
    dtiut = np.zeros(reference_image.shape + (6,), dtype=float)  
    dtivec = np.zeros(6, dtype=float)  
    it = np.ndindex( reference_image.shape )
    yyind=2
    xzind=3
    if upper_triangular:
        yyind=3
        xzind=2
    for i in it:
        dtix = tensorarray[i] # in ANTs - we have: [xx,xy,xz,yy,yz,zz]
        dtivec[0]=dtix[0,0]
        dtivec[yyind]=dtix[1,1] # 2 for LT
        dtivec[5]=dtix[2,2]
        dtivec[1]=dtix[0,1]
        dtivec[xzind]=dtix[2,0] # 3 for LT
        dtivec[4]=dtix[1,2]
        dtiut[i]=dtivec
    dtiAnts = ants.from_numpy( dtiut, has_components=True )
    ants.copy_image_info( reference_image, dtiAnts )
    return dtiAnts




# template_figure_with_overlay - 97 lines
def template_figure_with_overlay(scalar_label_df, prefix, outputfilename=None, template='cit168', xyz=None, mask_dilation=25, padding=12, verbose=True):
    """
    Process and visualize images with mapped scalar values.

    Parameters:
    - scalar_label_df (pd.DataFrame): A Pandas DataFrame containing scalar values and labels.
    - prefix (str): The prefix for input image files.
    - template (str, optional): Template for selecting image data (default is 'cit168').
    - xyz (str, optional): The integer index of the slices to display.
    - mask_dilation (int, optional): Dilation factor for creating a mask (default is 25).
    - padding (int, optional): Padding value for the mapped images (default is 12).
    - verbose (bool, optional): Enable verbose mode for printing (default is True).

    Example Usage:
    >>> scalar_label_df = pd.DataFrame({'label': [1, 2, 3], 'scalar_value': [0.5, 0.8, 1.2]})
    >>> prefix = '../PPMI_template0_'
    >>> process_and_visualize_images(scalar_label_df, prefix, template='cit168', xyz=None, mask_dilation=25, padding=12, verbose=True)
    """

    # Template image paths
    template_paths = {
        'cit168': 'cit168lab.nii.gz',
        'bf': 'bf.nii.gz',
        'cerebellum': 'cerebellum.nii.gz',
        'mtl': 'mtl.nii.gz',
        'ctx': 'dkt_cortex.nii.gz',
        'jhuwm': 'JHU_wm.nii.gz'
    }

    if template not in template_paths:
        print( "Valid options:")
        print( template_paths )
        raise ValueError(f"Template option '{template}' does not exist.")

    template_image_path = template_paths[template]
    template_image = ants.image_read(f'{prefix}{template_image_path}')

    # Load image data
    edgeimg = ants.image_read(f'{prefix}edge.nii.gz')
    dktimg = ants.image_read(f'{prefix}dkt_parcellation.nii.gz')
    segimg = ants.image_read(f'{prefix}tissue_segmentation.nii.gz')
    ttl = ''

    # Load and process the template image
    ventricles = ants.threshold_image(dktimg, 4, 4) + ants.threshold_image(dktimg, 43, 43)
    seggm = ants.mask_image(segimg, segimg, [2, 4], binarize=False)
    edgeimg = edgeimg.clone()
    edgeimg[edgeimg == 0] = ventricles[edgeimg == 0]
    segwm = ants.threshold_image(segimg, 3, 4).morphology("open", 1)

    # Define cropping mask
    cmask = ants.threshold_image(template_image, 1, 1.e9).iMath("MD", mask_dilation)

    mapped_image = map_scalar_to_labels(scalar_label_df, template_image)
    tcrop = ants.crop_image(template_image, cmask)
    toviz = ants.crop_image(mapped_image, cmask)
    seggm = ants.crop_image(edgeimg, cmask)
       
    # Map scalar values to labels and visualize
    toviz = ants.pad_image(toviz, pad_width=(padding, padding, padding))
    seggm = ants.pad_image(seggm, pad_width=(padding, padding, padding))
    tcrop = ants.pad_image(tcrop, pad_width=(padding, padding, padding))

    if xyz is None:
        if template == 'cit168':
            xyz=[140, 89, 94]
        elif template == 'bf':
            xyz=[114,92,76]
        elif template == 'cerebellum':
            xyz=[169, 128, 137]
        elif template == 'mtl':
            xyz=[154, 112, 113]
        elif template == 'ctx':
            xyz=[233, 190, 174]
        elif template == 'jhuwm':
            xyz=[146, 133, 182]

    if verbose:
        print("plot xyz for " + template )
        print( xyz )
        
    if outputfilename is None:
        temp = ants.plot_ortho( seggm, overlay=toviz, crop=False,
                        xyz=xyz, cbar_length=0.2, cbar_vertical=False,
                        flat=True, xyz_lines=False, resample=False, orient_labels=False,
                        title=ttl, titlefontsize=12, title_dy=-0.02, textfontcolor='red', 
                        cbar=True, allow_xyz_change=False)
    else:
        temp = ants.plot_ortho( seggm, overlay=toviz, crop=False,
                    xyz=xyz, cbar_length=0.2, cbar_vertical=False,
                    flat=True, xyz_lines=False, resample=False, orient_labels=False,
                    title=ttl, titlefontsize=12, title_dy=-0.02, textfontcolor='red', 
                    cbar=True, allow_xyz_change=False, filename=outputfilename )
    seggm = temp['image']
    toviz = temp['overlay']
    return { "underlay": seggm, 'overlay': toviz, 'seg': tcrop  }



# dewarp_imageset - 105 lines
def dewarp_imageset( image_list, initial_template=None,
    iterations=None, padding=0, target_idx=[0], **kwargs ):
    """
    Dewarp a set of images

    Makes simplifying heuristic decisions about how to transform an image set
    into an unbiased reference space.  Will handle plenty of decisions
    automatically so beware.  Computes an average shape space for the images
    and transforms them to that space.

    Arguments
    ---------
    image_list : list containing antsImages 2D, 3D or 4D

    initial_template : optional

    iterations : number of template building iterations

    padding:  will pad the images by an integer amount to limit edge effects

    target_idx : the target indices for the time series over which we should average;
        a list of integer indices into the last axis of the input images.

    kwargs : keyword args
        arguments passed to ants registration - these must be set explicitly

    Returns
    -------
    a dictionary with the mean image and the list of the transformed images as
    well as motion correction parameters for each image in the input list

    Example
    -------
    >>> import antspymm
    """
    outlist = []
    avglist = []
    if len(image_list[0].shape) > 3:
        imagetype = 3
        for k in range(len(image_list)):
            for j in range(len(target_idx)):
                avglist.append( ants.slice_image( image_list[k], axis=3, idx=target_idx[j] ) )
    else:
        imagetype = 0
        avglist=image_list

    pw=[]
    for k in range(len(avglist[0].shape)):
        pw.append( padding )
    for k in range(len(avglist)):
        avglist[k] = ants.pad_image( avglist[k], pad_width=pw  )

    if initial_template is None:
        initial_template = avglist[0] * 0
        for k in range(len(avglist)):
            initial_template = initial_template + avglist[k]/len(avglist)

    if iterations is None:
        iterations = 2

    btp = ants.build_template(
        initial_template=initial_template,
        image_list=avglist,
        gradient_step=0.5, blending_weight=0.8,
        iterations=iterations, verbose=False, **kwargs )

    # last - warp all images to this frame
    mocoplist = []
    mocofdlist = []
    reglist = []
    for k in range(len(image_list)):
        if imagetype == 3:
            moco0 = ants.motion_correction( image=image_list[k], fixed=btp, type_of_transform='antsRegistrationSyNRepro[r]' )
            mocoplist.append( moco0['motion_parameters'] )
            mocofdlist.append( moco0['FD'] )
            locavg = ants.slice_image( moco0['motion_corrected'], axis=3, idx=0 ) * 0.0
            for j in range(len(target_idx)):
                locavg = locavg + ants.slice_image( moco0['motion_corrected'], axis=3, idx=target_idx[j] )
            locavg = locavg * 1.0 / len(target_idx)
        else:
            locavg = image_list[k]
        reg = ants.registration( btp, locavg, **kwargs )
        reglist.append( reg )
        if imagetype == 3:
            myishape = image_list[k].shape
            mytslength = myishape[ len(myishape) - 1 ]
            mywarpedlist = []
            for j in range(mytslength):
                locimg = ants.slice_image( image_list[k], axis=3, idx = j )
                mywarped = ants.apply_transforms( btp, locimg,
                    reg['fwdtransforms'] + moco0['motion_parameters'][j], imagetype=0 )
                mywarpedlist.append( mywarped )
            mywarped = ants.list_to_ndimage( image_list[k], mywarpedlist )
        else:
            mywarped = ants.apply_transforms( btp, image_list[k], reg['fwdtransforms'], imagetype=imagetype )
        outlist.append( mywarped )

    return {
        'dewarpedmean':btp,
        'dewarped':outlist,
        'deformable_registrations': reglist,
        'FD': mocofdlist,
        'motionparameters': mocoplist }




# super_res_mcimage - 83 lines
def super_res_mcimage( image,
    srmodel,
    truncation=[0.0001,0.995],
    poly_order='hist',
    target_range=[0,1],
    isotropic = False,
    verbose=False ):
    """
    Super resolution on a timeseries or multi-channel image

    Arguments
    ---------
    image : an antsImage

    srmodel : a tensorflow fully convolutional model

    truncation :  quantiles at which we truncate intensities to limit impact of outliers e.g. [0.005,0.995]

    poly_order : if not None, will fit a global regression model to map
        intensity back to original histogram space; if 'hist' will match
        by histogram matching - ants.histogram_match_image

    target_range : 2-element tuple
        a tuple or array defining the (min, max) of the input image
        (e.g., [-127.5, 127.5] or [0,1]).  Output images will be scaled back to original
        intensity. This range should match the mapping used in the training
        of the network.

    isotropic : boolean

    verbose : boolean

    Returns
    -------
    super resolution version of the image

    Example
    -------
    >>> import antspymm
    """
    idim = image.dimension
    ishape = image.shape
    nTimePoints = ishape[idim - 1]
    mcsr = list()
    for k in range(nTimePoints):
        if verbose and (( k % 5 ) == 0 ):
            mycount = round(k / nTimePoints * 100)
            print(mycount, end="%.", flush=True)
        temp = ants.slice_image( image, axis=idim - 1, idx=k )
        temp = ants.iMath( temp, "TruncateIntensity", truncation[0], truncation[1] )
        mysr = antspynet.apply_super_resolution_model_to_image( temp, srmodel,
            target_range = target_range )
        if poly_order is not None:
            bilin = ants.resample_image_to_target( temp, mysr )
            if poly_order == 'hist':
                mysr = ants.histogram_match_image( mysr, bilin )
            else:
                mysr = ants.regression_match_image( mysr, bilin, poly_order = poly_order )
        if isotropic:
            mysr = down2iso( mysr )
        if k == 0:
            upshape = list()
            for j in range(len(ishape)-1):
                upshape.append( mysr.shape[j] )
            upshape.append( ishape[ idim-1 ] )
            if verbose:
                print("SR will be of voxel size:" + str(upshape) )
        mcsr.append( mysr )

    upshape = list()
    for j in range(len(ishape)-1):
        upshape.append( mysr.shape[j] )
    upshape.append( ishape[ idim-1 ] )
    if verbose:
        print("SR will be of voxel size:" + str(upshape) )

    imageup = ants.resample_image( image, upshape, use_voxels = True )
    if verbose:
        print("Done")

    return ants.list_to_ndimage( imageup, mcsr )




# neuromelanin - 198 lines
def neuromelanin( list_nm_images, t1, t1_head, t1lab, brain_stem_dilation=8,
    bias_correct=True,
    denoise=None,
    srmodel=None,
    target_range=[0,1],
    poly_order='hist',
    normalize_nm = False,
    verbose=False ) :

  """
  Outputs the averaged and registered neuromelanin image, and neuromelanin labels

  Arguments
  ---------
  list_nm_image : list of ANTsImages
    list of neuromenlanin repeat images

  t1 : ANTsImage
    input 3-D T1 brain image

  t1_head : ANTsImage
    input 3-D T1 head image

  t1lab : ANTsImage
    t1 labels that will be propagated to the NM

  brain_stem_dilation : integer default 8
    dilates the brain stem mask to better match coverage of NM

  bias_correct : boolean

  denoise : None or integer

  srmodel : None -- this is a work in progress feature, probably not optimal

  target_range : 2-element tuple
        a tuple or array defining the (min, max) of the input image
        (e.g., [-127.5, 127.5] or [0,1]).  Output images will be scaled back to original
        intensity. This range should match the mapping used in the training
        of the network.

  poly_order : if not None, will fit a global regression model to map
      intensity back to original histogram space; if 'hist' will match
      by histogram matching - ants.histogram_match_image

  normalize_nm : boolean - WIP not validated

  verbose : boolean

  Returns
  ---------
  Averaged and registered neuromelanin image and neuromelanin labels and wide csv

  """

  fnt=os.path.expanduser("~/.antspyt1w/CIT168_T1w_700um_pad_adni.nii.gz" )
  fntNM=os.path.expanduser("~/.antspymm/CIT168_T1w_700um_pad_adni_NM_norm_avg.nii.gz" )
  fntbst=os.path.expanduser("~/.antspyt1w/CIT168_T1w_700um_pad_adni_brainstem.nii.gz")
  fnslab=os.path.expanduser("~/.antspyt1w/CIT168_MT_Slab_adni.nii.gz")
  fntseg=os.path.expanduser("~/.antspyt1w/det_atlas_25_pad_LR_adni.nii.gz")

  template = mm_read( fnt )
  templateNM = ants.iMath( mm_read( fntNM ), "Normalize" )
  templatebstem = mm_read( fntbst ).threshold_image( 1, 1000 )
  # reg = ants.registration( t1, template, 'antsRegistrationSyNQuickRepro[s]' )
  reg = ants.registration( t1, template, 'antsRegistrationSyNQuickRepro[s]' )
  # map NM avg to t1 for neuromelanin processing
  nmavg2t1 = ants.apply_transforms( t1, templateNM,
    reg['fwdtransforms'], interpolator='linear' )
  slab2t1 = ants.threshold_image( nmavg2t1, "Otsu", 2 ).threshold_image(1,2).iMath("MD",1).iMath("FillHoles")
  # map brain stem and slab to t1 for neuromelanin processing
  bstem2t1 = ants.apply_transforms( t1, templatebstem,
    reg['fwdtransforms'],
    interpolator='nearestNeighbor' ).iMath("MD",1)
  slab2t1B = ants.apply_transforms( t1, mm_read( fnslab ),
    reg['fwdtransforms'], interpolator = 'nearestNeighbor')
  bstem2t1 = ants.crop_image( bstem2t1, slab2t1 )
  cropper = ants.decrop_image( bstem2t1, slab2t1 ).iMath("MD",brain_stem_dilation)

  # Average images in image_list
  nm_avg = list_nm_images[0]*0.0
  for k in range(len( list_nm_images )):
    if denoise is not None:
        list_nm_images[k] = ants.denoise_image( list_nm_images[k],
            shrink_factor=1,
            p=denoise,
            r=denoise+1,
            noise_model='Gaussian' )
    if bias_correct :
        n4mask = ants.threshold_image( ants.iMath(list_nm_images[k], "Normalize" ), 0.05, 1 )
        list_nm_images[k] = ants.n4_bias_field_correction( list_nm_images[k], mask=n4mask )
    nm_avg = nm_avg + ants.resample_image_to_target( list_nm_images[k], nm_avg ) / len( list_nm_images )

  if verbose:
      print("Register each nm image in list_nm_images to the averaged nm image (avg)")
  nm_avg_new = nm_avg * 0.0
  txlist = []
  for k in range(len( list_nm_images )):
    if verbose:
        print(str(k) + " of " + str(len( list_nm_images ) ) )
    current_image = ants.registration( list_nm_images[k], nm_avg,
        type_of_transform = 'antsRegistrationSyNRepro[r]' )
    txlist.append( current_image['fwdtransforms'][0] )
    current_image = current_image['warpedfixout']
    nm_avg_new = nm_avg_new + current_image / len( list_nm_images )
  nm_avg = nm_avg_new

  if verbose:
      print("do slab registration to map anatomy to NM space")
  t1c = ants.crop_image( t1_head, slab2t1 ).iMath("Normalize") # old way
  nmavg2t1c = ants.crop_image( nmavg2t1, slab2t1 ).iMath("Normalize")
  # slabreg = ants.registration( nm_avg, nmavg2t1c, 'antsRegistrationSyNRepro[r]' )
  slabreg = tra_initializer( nm_avg, t1c, verbose=verbose )
  if False:
      slabregT1 = tra_initializer( nm_avg, t1c, verbose=verbose  )
      miNM = ants.image_mutual_information( ants.iMath(nm_avg,"Normalize"),
            ants.iMath(slabreg0['warpedmovout'],"Normalize") )
      miT1 = ants.image_mutual_information( ants.iMath(nm_avg,"Normalize"),
            ants.iMath(slabreg1['warpedmovout'],"Normalize") )
      if miT1 < miNM:
        slabreg = slabregT1
  labels2nm = ants.apply_transforms( nm_avg, t1lab, slabreg['fwdtransforms'],
    interpolator = 'genericLabel' )
  cropper2nm = ants.apply_transforms( nm_avg, cropper, slabreg['fwdtransforms'], interpolator='nearestNeighbor' )
  nm_avg_cropped = ants.crop_image( nm_avg, cropper2nm )

  if verbose:
      print("now map these labels to each individual nm")
  crop_mask_list = []
  crop_nm_list = []
  for k in range(len( list_nm_images )):
      concattx = []
      concattx.append( txlist[k] )
      concattx.append( slabreg['fwdtransforms'][0] )
      cropmask = ants.apply_transforms( list_nm_images[k], cropper,
        concattx, interpolator = 'nearestNeighbor' )
      crop_mask_list.append( cropmask )
      temp = ants.crop_image( list_nm_images[k], cropmask )
      crop_nm_list.append( temp )

  if srmodel is not None:
      if verbose:
          print( " start sr " + str(len( crop_nm_list )) )
      for k in range(len( crop_nm_list )):
          if verbose:
              print( " do sr " + str(k) )
              print( crop_nm_list[k] )
          temp = antspynet.apply_super_resolution_model_to_image(
                crop_nm_list[k], srmodel, target_range=target_range,
                regression_order=None )
          if poly_order is not None:
              bilin = ants.resample_image_to_target( crop_nm_list[k], temp )
              if poly_order == 'hist':
                  temp = ants.histogram_match_image( temp, bilin )
              else:
                  temp = antspynet.regression_match_image( temp, bilin, poly_order = poly_order )
          crop_nm_list[k] = temp

  nm_avg_cropped = crop_nm_list[0]*0.0
  if verbose:
      print( "cropped average" )
      print( nm_avg_cropped )
  for k in range(len( crop_nm_list )):
      nm_avg_cropped = nm_avg_cropped + ants.apply_transforms( nm_avg_cropped,
        crop_nm_list[k], txlist[k] ) / len( crop_nm_list )
  for loop in range( 3 ):
      nm_avg_cropped_new = nm_avg_cropped * 0.0
      for k in range(len( crop_nm_list )):
            myreg = ants.registration(
                ants.iMath(nm_avg_cropped,"Normalize"),
                ants.iMath(crop_nm_list[k],"Normalize"),
                'antsRegistrationSyNRepro[r]' )
            warpednext = ants.apply_transforms(
                nm_avg_cropped_new,
                crop_nm_list[k],
                myreg['fwdtransforms'] )
            nm_avg_cropped_new = nm_avg_cropped_new + warpednext
      nm_avg_cropped = nm_avg_cropped_new / len( crop_nm_list )

  slabregUpdated = tra_initializer( nm_avg_cropped, t1c, compreg=slabreg,verbose=verbose  )
  tempOrig = ants.apply_transforms( nm_avg_cropped_new, t1c, slabreg['fwdtransforms'] )
  tempUpdate = ants.apply_transforms( nm_avg_cropped_new, t1c, slabregUpdated['fwdtransforms'] )
  miUpdate = ants.image_mutual_information(
    ants.iMath(nm_avg_cropped,"Normalize"), ants.iMath(tempUpdate,"Normalize") )
  miOrig = ants.image_mutual_information(
    ants.iMath(nm_avg_cropped,"Normalize"), ants.iMath(tempOrig,"Normalize") )
  if miUpdate < miOrig :
      slabreg = slabregUpdated

  if normalize_nm:
      nm_avg_cropped = ants.iMath( nm_avg_cropped, "Normalize" )
      nm_avg_cropped = ants.iMath( nm_avg_cropped, "TruncateIntensity",0.05,0.95)
      nm_avg_cropped = ants.iMath( nm_avg_cropped, "Normalize" )

  labels2nm = ants.apply_transforms( nm_avg_cropped, t1lab,
        slabreg['fwdtransforms'], interpolator='nearestNeighbor' )

  # fix the reference region - keep top two parts


# bold_perfusion_minimal - 219 lines
def bold_perfusion_minimal( 
        fmri, 
        m0_image = None,
        spa = (0., 0., 0., 0.),
        nc  = 0,
        tc='alternating',
        n_to_trim=0,
        outlier_threshold=0.250,
        plot_brain_mask=False,
        verbose=False ):
  """
  Estimate perfusion from a BOLD time series image.  Will attempt to figure out the T-C labels from the data.  The function uses defaults to quantify CBF but these will usually not be correct for your own data.  See the function calculate_CBF for an example of how one might do quantification based on the outputs of this function specifically the perfusion, m0 and mask images that are part of the output dictionary.

  This function is intended for use in debugging/testing or when one lacks a T1w image.

  Arguments
  ---------

  fmri : BOLD fmri antsImage

  m0_image: a pre-defined m0 antsImage

  spa : gaussian smoothing for spatial and temporal component e.g. (1,1,1,0) in physical space coordinates

  nc  : number of components for compcor filtering

  tc: string either alternating or split (default is alternating ie CTCTCT; split is CCCCTTTT)

  n_to_trim: number of volumes to trim off the front of the time series to account for initial magnetic saturation effects or to allow the signal to reach a steady state. in some cases, trailing volumes or other outlier volumes may need to be rejected.  this code does not currently handle that issue.

  outlier_threshold (numeric): between zero (remove all) and one (remove none); automatically calculates outlierness and uses it to censor the time series.

  plot_brain_mask : boolean can help with checking data quality visually

  verbose : boolean

  Returns
  ---------
  a dictionary containing the derived network maps

  """
  import numpy as np
  import pandas as pd
  import re
  import math
  from sklearn.linear_model import RANSACRegressor, TheilSenRegressor, HuberRegressor, QuantileRegressor, LinearRegression, SGDRegressor
  from sklearn.multioutput import MultiOutputRegressor
  from sklearn.preprocessing import StandardScaler

  def replicate_list(user_list, target_size):
    # Calculate the number of times the list should be replicated
    replication_factor = target_size // len(user_list)
    # Replicate the list and handle any remaining elements
    replicated_list = user_list * replication_factor
    remaining_elements = target_size % len(user_list)
    replicated_list += user_list[:remaining_elements]
    return replicated_list

  A = np.zeros((1,1))
  fmri_template = ants.get_average_of_timeseries( fmri )
  if n_to_trim is None:
    n_to_trim=0
  mytrim=n_to_trim
  perf_total_sigma = 1.5
  corrmo = timeseries_reg(
    fmri, fmri_template,
    type_of_transform='antsRegistrationSyNRepro[r]',
    total_sigma=perf_total_sigma,
    fdOffset=2.0,
    trim = mytrim,
    output_directory=None,
    verbose=verbose,
    syn_metric='CC',
    syn_sampling=2,
    reg_iterations=[40,20,5] )
  if verbose:
      print("End rsfmri motion correction")
      print("--maximum motion : " + str(corrmo['FD'].max()) )

  if m0_image is not None:
      m0 = m0_image

  ntp = corrmo['motion_corrected'].shape[3]
  fmri_template = ants.get_average_of_timeseries( corrmo['motion_corrected'] )
  bmask = antspynet.brain_extraction( fmri_template, 'bold' ).threshold_image(0.5,1).iMath("GetLargestComponent").morphology("close",2).iMath("FillHoles")
  if plot_brain_mask:
    ants.plot( fmri_template, bmask, axis=1, crop=True )
    ants.plot( fmri_template, bmask, axis=2, crop=True )

  if tc == 'alternating':
      tclist = replicate_list( ['C','T'], ntp )
  else:
      tclist = replicate_list( ['C'], int(ntp/2) ) + replicate_list( ['T'],  int(ntp/2) )

  tclist = one_hot_encode( tclist[0:ntp ] )
  fmrimotcorr=corrmo['motion_corrected']
  hlinds = None
  if outlier_threshold < 1.0 and outlier_threshold > 0.0:
    fmrimotcorr, hlinds = loop_timeseries_censoring( fmrimotcorr, outlier_threshold, mask=None, verbose=verbose )
    tclist = remove_elements_from_numpy_array( tclist, hlinds)
    corrmo['FD'] = remove_elements_from_numpy_array( corrmo['FD'], hlinds )

  # redo template and registration at (potentially) upsampled scale
  fmri_template = ants.iMath( ants.get_average_of_timeseries( fmrimotcorr ), "Normalize" )
  corrmo = timeseries_reg(
        fmri, fmri_template,
        type_of_transform='antsRegistrationSyNRepro[r]',
        total_sigma=perf_total_sigma,
        fdOffset=2.0,
        trim = mytrim,
        output_directory=None,
        verbose=verbose,
        syn_metric='CC',
        syn_sampling=2,
        reg_iterations=[40,20,5] )
  if verbose:
        print("End 2nd rsfmri motion correction")
        print("--maximum motion : " + str(corrmo['FD'].max()) )

  if outlier_threshold < 1.0 and outlier_threshold > 0.0:
    corrmo['motion_corrected'] = remove_volumes_from_timeseries( corrmo['motion_corrected'], hlinds )
    corrmo['FD'] = remove_elements_from_numpy_array( corrmo['FD'], hlinds )

  bmask = antspynet.brain_extraction( fmri_template, 'bold' ).threshold_image(0.5,1).iMath("GetLargestComponent").morphology("close",2).iMath("FillHoles")
  if plot_brain_mask:
    ants.plot( fmri_template, bmask, axis=1, crop=True )
    ants.plot( fmri_template, bmask, axis=2, crop=True )

  regression_mask = bmask.clone()
  mytsnr = tsnr( corrmo['motion_corrected'], bmask )
  mytsnrThresh = np.quantile( mytsnr.numpy(), 0.995 )
  tsnrmask = ants.threshold_image( mytsnr, 0, mytsnrThresh ).morphology("close",3)
  bmask = bmask * ants.iMath( tsnrmask, "FillHoles" )
  fmrimotcorr=corrmo['motion_corrected']
  und = fmri_template * bmask
  compcorquantile=0.50
  mycompcor = ants.compcor( fmrimotcorr,
    ncompcor=nc, quantile=compcorquantile, mask = bmask,
    filter_type='polynomial', degree=2 )
  tr = ants.get_spacing( fmrimotcorr )[3]
  simg = ants.smooth_image(fmrimotcorr, spa, sigma_in_physical_coordinates = True )
  nuisance = mycompcor['basis']
  nuisance = np.c_[ nuisance, mycompcor['components'] ]
  if verbose:
    print("make sure nuisance is independent of TC")
  nuisance = ants.regress_components( nuisance, tclist )
  regression_mask = bmask.clone()
  gmmat = ants.timeseries_to_matrix( simg, regression_mask )
  regvars = np.hstack( (nuisance, tclist ))
  coefind = regvars.shape[1]-1
  regvars = regvars[:,range(coefind)]
  predictor_of_interest_idx = regvars.shape[1]-1
  valid_perf_models = ['huber','quantile','theilsen','ransac', 'sgd', 'linear','SM']
  perfusion_regression_model='linear'
  if verbose:
    print( "begin perfusion estimation with " + perfusion_regression_model + " model " )
  regression_model = LinearRegression()
  regression_model.fit( regvars, gmmat )
  coefind = regression_model.coef_.shape[1]-1
  perfimg = ants.make_image( regression_mask, regression_model.coef_[:,coefind] )
  gmseg = ants.image_clone( bmask )
  meangmval = ( perfimg[ gmseg == 1 ] ).mean()
  if meangmval < 0:
      perfimg = perfimg * (-1.0)
  negative_voxels = ( perfimg < 0.0 ).sum() / np.prod( perfimg.shape ) * 100.0
  perfimg[ perfimg < 0.0 ] = 0.0 # non-physiological

  if m0_image is None:
    m0 = ants.get_average_of_timeseries( fmrimotcorr )
  else:
    # register m0 to current template
    m0reg = ants.registration( fmri_template, m0, 'antsRegistrationSyNRepro[r]', verbose=False )
    m0 = m0reg['warpedmovout']

  if ntp == 2 :
      img0 = ants.slice_image( corrmo['motion_corrected'], axis=3, idx=0 )
      img1 = ants.slice_image( corrmo['motion_corrected'], axis=3, idx=1 )
      if m0_image is None:
        if img0.mean() < img1.mean():
            perfimg=img0
            m0=img1
        else:
            perfimg=img1
            m0=img0
      else:
        if img0.mean() < img1.mean():
            perfimg=img1-img0
        else:
            perfimg=img0-img1
  
  cbf = calculate_CBF( Delta_M=perfimg, M_0=m0, mask=bmask )
  meangmval = ( perfimg[ gmseg == 1 ] ).mean()        
  meangmvalcbf = ( cbf[ gmseg == 1 ] ).mean()
  if verbose:
    print("perfimg.max() " + str(  perfimg.max() ) )
  outdict = {}
  outdict['meanBold'] = und
  outdict['brainmask'] = bmask
  rsfNuisance = pd.DataFrame( nuisance )
  rsfNuisance['FD']=corrmo['FD']
  outdict['perfusion']=perfimg
  outdict['cbf']=cbf
  outdict['m0']=m0
  outdict['perfusion_gm_mean']=meangmval
  outdict['cbf_gm_mean']=meangmvalcbf
  outdict['motion_corrected'] = corrmo['motion_corrected']
  outdict['brain_mask'] = bmask
  outdict['nuisance'] = rsfNuisance
  outdict['tsnr'] = mytsnr
  outdict['dvars'] = dvars( corrmo['motion_corrected'], gmseg )
  outdict['FD_max'] = rsfNuisance['FD'].max()
  outdict['FD_mean'] = rsfNuisance['FD'].mean()
  outdict['FD_sd'] = rsfNuisance['FD'].std()
  outdict['outlier_volumes']=hlinds
  outdict['negative_voxels']=negative_voxels
  return convert_np_in_dict( outdict )





# bold_perfusion - 314 lines
def bold_perfusion( 
    fmri, t1head, t1, t1segmentation, t1dktcit,
                   FD_threshold=0.5,
                   spa = (0., 0., 0., 0.),
                   nc = 3,
                   type_of_transform='antsRegistrationSyNRepro[r]',
                   tc='alternating',
                   n_to_trim=0,
                   m0_image = None,
                   m0_indices=None,
                   outlier_threshold=0.250,
                   add_FD_to_nuisance=False,
                   n3=False,
                   segment_timeseries=False,
                   trim_the_mask=4.25,
                   upsample=True,
                   perfusion_regression_model='linear',
                   verbose=False ):
  """
  Estimate perfusion from a BOLD time series image.  Will attempt to figure out the T-C labels from the data.  The function uses defaults to quantify CBF but these will usually not be correct for your own data.  See the function calculate_CBF for an example of how one might do quantification based on the outputs of this function specifically the perfusion, m0 and mask images that are part of the output dictionary.

  Arguments
  ---------
  fmri : BOLD fmri antsImage

  t1head : ANTsImage
    input 3-D T1 brain image (not brain extracted)

  t1 : ANTsImage
    input 3-D T1 brain image (brain extracted)

  t1segmentation : ANTsImage
    t1 segmentation - a six tissue segmentation image in T1 space

  t1dktcit : ANTsImage
    t1 dkt cortex plus cit parcellation

  spa : gaussian smoothing for spatial and temporal component e.g. (1,1,1,0) in physical space coordinates

  nc  : number of components for compcor filtering

  type_of_transform : SyN or Rigid

  tc: string either alternating or split (default is alternating ie CTCTCT; split is CCCCTTTT)

  n_to_trim: number of volumes to trim off the front of the time series to account for initial magnetic saturation effects or to allow the signal to reach a steady state. in some cases, trailing volumes or other outlier volumes may need to be rejected.  this code does not currently handle that issue.

  m0_image: a pre-defined m0 image - we expect this to be 3D.  if it is not, we naively 
    average over the 4th dimension.

  m0_indices: which indices in the perfusion image are the m0.  if set, n_to_trim will be ignored.

  outlier_threshold (numeric): between zero (remove all) and one (remove none); automatically calculates outlierness and uses it to censor the time series.

  add_FD_to_nuisance: boolean

  n3: boolean

  segment_timeseries : boolean

  trim_the_mask : float >= 0 post-hoc method for trimming the mask

  upsample: boolean

  perfusion_regression_model: string 'linear', 'ransac', 'theilsen', 'huber', 'quantile', 'sgd'; 'linear' and 'huber' are the only ones that work ok by default and are relatively quick to compute.

  verbose : boolean

  Returns
  ---------
  a dictionary containing the derived network maps

  """
  import numpy as np
  import pandas as pd
  import re
  import math
  from sklearn.linear_model import RANSACRegressor, TheilSenRegressor, HuberRegressor, QuantileRegressor, LinearRegression, SGDRegressor
  from sklearn.multioutput import MultiOutputRegressor
  from sklearn.preprocessing import StandardScaler

  # remove outlier volumes
  if segment_timeseries:
    lo_vs_high = segment_timeseries_by_meanvalue(fmri)
    fmri = remove_volumes_from_timeseries( fmri, lo_vs_high['lowermeans'] )

  ex_path = os.path.expanduser( "~/.antspyt1w/" )
  cnxcsvfn = ex_path + "dkt_cortex_cit_deep_brain.csv"

  if n3:
    fmri = timeseries_n3( fmri )

  if m0_image is not None:
    if m0_image.dimension == 4:
      m0_image = ants.get_average_of_timeseries( m0_image )

  def select_regression_model(regression_model, min_samples=10 ):
    if regression_model == 'sgd' :
      sgd_regressor = SGDRegressor(penalty='elasticnet', alpha=1e-5, l1_ratio=0.15, max_iter=20000, tol=1e-3, random_state=42)
      return sgd_regressor
    elif regression_model == 'ransac':
      ransac = RANSACRegressor(
            min_samples=0.8,
            max_trials=10,         # Maximum number of iterations
#            min_samples=min_samples, # Minimum number samples to be chosen as inliers in each iteration
#            stop_probability=0.80,  # Probability to stop the algorithm if a good subset is found
#            stop_n_inliers=40,      # Stop if this number of inliers is found
#            stop_score=0.8,         # Stop if the model score reaches this value
#            n_jobs=int(os.getenv("ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS")) # Use all available CPU cores for parallel processing
        )
      return ransac
    models = {
        'sgd':SGDRegressor,
        'ransac': RANSACRegressor,
        'theilsen': TheilSenRegressor,
        'huber': HuberRegressor,
        'quantile': QuantileRegressor
    }
    return models.get(regression_model.lower(), LinearRegression)()

  def replicate_list(user_list, target_size):
    # Calculate the number of times the list should be replicated
    replication_factor = target_size // len(user_list)
    # Replicate the list and handle any remaining elements
    replicated_list = user_list * replication_factor
    remaining_elements = target_size % len(user_list)
    replicated_list += user_list[:remaining_elements]
    return replicated_list

  A = np.zeros((1,1))
  # fmri = ants.iMath( fmri, 'Normalize' )
  fmri_template, hlinds = loop_timeseries_censoring( fmri, 0.10 )
  fmri_template = ants.get_average_of_timeseries( fmri_template )
  del hlinds
  rig = ants.registration( fmri_template, t1head, 'antsRegistrationSyNRepro[r]' )
  bmask = ants.apply_transforms( fmri_template, ants.threshold_image(t1segmentation,1,6), rig['fwdtransforms'][0], interpolator='genericLabel' )
  if m0_indices is None:
    if n_to_trim is None:
        n_to_trim=0
    mytrim=n_to_trim
  else:
    mytrim = 0
  perf_total_sigma = 1.5
  corrmo = timeseries_reg(
    fmri, fmri_template,
    type_of_transform=type_of_transform,
    total_sigma=perf_total_sigma,
    fdOffset=2.0,
    trim = mytrim,
    output_directory=None,
    verbose=verbose,
    syn_metric='CC',
    syn_sampling=2,
    reg_iterations=[40,20,5] )
  if verbose:
      print("End rsfmri motion correction")

  if m0_image is not None:
      m0 = m0_image
  elif m0_indices is not None:
    not_m0 = list( range( fmri.shape[3] ) )
    not_m0 = [x for x in not_m0 if x not in m0_indices]
    if verbose:
        print( m0_indices )
        print( not_m0 )
    # then remove it from the time series
    m0 = remove_volumes_from_timeseries( corrmo['motion_corrected'], not_m0 )
    m0 = ants.get_average_of_timeseries( m0 )
    corrmo['motion_corrected'] = remove_volumes_from_timeseries( 
        corrmo['motion_corrected'], m0_indices )
    corrmo['FD'] = remove_elements_from_numpy_array( corrmo['FD'], m0_indices )
    fmri = remove_volumes_from_timeseries( fmri, m0_indices )

  ntp = corrmo['motion_corrected'].shape[3]
  if tc == 'alternating':
      tclist = replicate_list( ['C','T'], ntp )
  else:
      tclist = replicate_list( ['C'], int(ntp/2) ) + replicate_list( ['T'],  int(ntp/2) )

  tclist = one_hot_encode( tclist[0:ntp ] )
  fmrimotcorr=corrmo['motion_corrected']
  if outlier_threshold < 1.0 and outlier_threshold > 0.0:
    fmrimotcorr, hlinds = loop_timeseries_censoring( fmrimotcorr, outlier_threshold, mask=None, verbose=verbose )
    tclist = remove_elements_from_numpy_array( tclist, hlinds)
    corrmo['FD'] = remove_elements_from_numpy_array( corrmo['FD'], hlinds )

  # redo template and registration at (potentially) upsampled scale
  fmri_template = ants.iMath( ants.get_average_of_timeseries( fmrimotcorr ), "Normalize" )
  if upsample:
      spc = ants.get_spacing( fmri )
      minspc = 2.0
      if min(spc[0:3]) < minspc:
          minspc = min(spc[0:3])
      newspc = [minspc,minspc,minspc]
      fmri_template = ants.resample_image( fmri_template, newspc, interp_type=0 )

  if verbose:
      print( 'fmri_template')
      print( fmri_template )

  rig = ants.registration( fmri_template, t1head, 'antsRegistrationSyNRepro[r]' )
  bmask = ants.apply_transforms( fmri_template, 
    ants.threshold_image(t1segmentation,1,6), 
    rig['fwdtransforms'][0], 
    interpolator='genericLabel' )

  warn_if_small_mask( bmask, label='bold_perfusion:bmask')

  corrmo = timeseries_reg(
        fmri, fmri_template,
        type_of_transform=type_of_transform,
        total_sigma=perf_total_sigma,
        fdOffset=2.0,
        trim = mytrim,
        output_directory=None,
        verbose=verbose,
        syn_metric='CC',
        syn_sampling=2,
        reg_iterations=[40,20,5] )
  if verbose:
        print("End 2nd rsfmri motion correction")

  if outlier_threshold < 1.0 and outlier_threshold > 0.0:
    corrmo['motion_corrected'] = remove_volumes_from_timeseries( corrmo['motion_corrected'], hlinds )
    corrmo['FD'] = remove_elements_from_numpy_array( corrmo['FD'], hlinds )

  regression_mask = bmask.clone()
  mytsnr = tsnr( corrmo['motion_corrected'], bmask )
  mytsnrThresh = np.quantile( mytsnr.numpy(), 0.995 )
  tsnrmask = ants.threshold_image( mytsnr, 0, mytsnrThresh ).morphology("close",3)
  bmask = bmask * ants.iMath( tsnrmask, "FillHoles" )
  warn_if_small_mask( bmask, label='bold_perfusion:bmask*tsnrmask')
  fmrimotcorr=corrmo['motion_corrected']
  und = fmri_template * bmask
  t1reg = ants.registration( und, t1, "antsRegistrationSyNRepro[s]" )
  gmseg = ants.threshold_image( t1segmentation, 2, 2 )
  gmseg = gmseg + ants.threshold_image( t1segmentation, 4, 4 )
  gmseg = ants.threshold_image( gmseg, 1, 4 )
  gmseg = ants.iMath( gmseg, 'MD', 1 )
  gmseg = ants.apply_transforms( und, gmseg,
    t1reg['fwdtransforms'], interpolator = 'genericLabel' ) * bmask
  csfseg = ants.threshold_image( t1segmentation, 1, 1 )
  wmseg = ants.threshold_image( t1segmentation, 3, 3 )
  csfAndWM = ( csfseg + wmseg ).morphology("erode",1)
  compcorquantile=0.50
  csfAndWM = ants.apply_transforms( und, csfAndWM,
    t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  csfseg = ants.apply_transforms( und, csfseg,
    t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  wmseg = ants.apply_transforms( und, wmseg,
    t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  warn_if_small_mask( wmseg, label='bold_perfusion:wmseg')
  # warn_if_small_mask( csfseg, threshold_fraction=0.01, label='bold_perfusion:csfseg')
  warn_if_small_mask( csfAndWM, label='bold_perfusion:csfAndWM')
  mycompcor = ants.compcor( fmrimotcorr,
    ncompcor=nc, quantile=compcorquantile, mask = csfAndWM,
    filter_type='polynomial', degree=2 )
  tr = ants.get_spacing( fmrimotcorr )[3]
  simg = ants.smooth_image(fmrimotcorr, spa, sigma_in_physical_coordinates = True )
  nuisance = mycompcor['basis']
  nuisance = np.c_[ nuisance, mycompcor['components'] ]
  if add_FD_to_nuisance:
    nuisance = np.c_[ nuisance, corrmo['FD'] ]
  if verbose:
    print("make sure nuisance is independent of TC")
  nuisance = ants.regress_components( nuisance, tclist )
  regression_mask = bmask.clone()
  gmmat = ants.timeseries_to_matrix( simg, regression_mask )
  regvars = np.hstack( (nuisance, tclist ))
  coefind = regvars.shape[1]-1
  regvars = regvars[:,range(coefind)]
  predictor_of_interest_idx = regvars.shape[1]-1
  valid_perf_models = ['huber','quantile','theilsen','ransac', 'sgd', 'linear','SM']
  if verbose:
    print( "begin perfusion estimation with " + perfusion_regression_model + " model " )
  if perfusion_regression_model == 'linear':
    regression_model = LinearRegression()
    regression_model.fit( regvars, gmmat )
    coefind = regression_model.coef_.shape[1]-1
    perfimg = ants.make_image( regression_mask, regression_model.coef_[:,coefind] )
  elif perfusion_regression_model == 'SM': #
    import statsmodels.api as sm
    coeffs = np.zeros( gmmat.shape[1] )
    # Loop over each outcome column in the outcomes matrix
    for outcome_idx in range(gmmat.shape[1]):
        outcome = gmmat[:, outcome_idx]  # Select one outcome column
        model = sm.RLM(outcome, sm.add_constant(regvars), M=sm.robust.norms.HuberT())  # Huber's T norm for robust regression
        results = model.fit()
        coefficients = results.params  # Coefficients of all predictors
        coeffs[outcome_idx] = coefficients[predictor_of_interest_idx]
    perfimg = ants.make_image( regression_mask, coeffs )
  elif perfusion_regression_model in valid_perf_models :
    scaler = StandardScaler()
    gmmat = scaler.fit_transform(gmmat)
    coeffs = np.zeros( gmmat.shape[1] )
    huber_regressor = select_regression_model( perfusion_regression_model )
    multioutput_model = MultiOutputRegressor(huber_regressor)
    multioutput_model.fit( regvars, gmmat )
    ct=0
    for i, estimator in enumerate(multioutput_model.estimators_):
      coefficients = estimator.coef_
      coeffs[ct]=coefficients[predictor_of_interest_idx]
      ct=ct+1
    perfimg = ants.make_image( regression_mask, coeffs )
  else:
    raise ValueError( perfusion_regression_model + " regression model is not found.")
  meangmval = ( perfimg[ gmseg == 1 ] ).mean()
  if meangmval < 0:
      perfimg = perfimg * (-1.0)
  negative_voxels = ( perfimg < 0.0 ).sum() / np.prod( perfimg.shape ) * 100.0
  perfimg[ perfimg < 0.0 ] = 0.0 # non-physiological

  # LaTeX code for Cerebral Blood Flow (CBF) calculation using ASL MRI
  """


# crop_mcimage - 30 lines
def crop_mcimage( x, mask, padder=None ):
    """
    crop a time series (4D) image by a 3D mask

    Parameters
    -------------

    x : raw image

    mask  : mask for cropping

    """
    cropmask = ants.crop_image( mask, mask )
    myorig = list( ants.get_origin(cropmask) )
    myorig.append( ants.get_origin( x )[3] )
    croplist = []
    if len(x.shape) > 3:
        for k in range(x.shape[3]):
            temp = ants.slice_image( x, axis=3, idx=k )
            temp = ants.crop_image( temp, mask )
            if padder is not None:
                temp = ants.pad_image( temp, pad_width=padder )
            croplist.append( temp )
        temp = ants.list_to_ndimage( x, croplist )
        temp.set_origin( myorig )
        return temp
    else:
        return( ants.crop_image( x, mask ) )




# alff_image - 34 lines
def alff_image( x, mask, flo=0.01, fhi=0.1, nuisance=None ):
    """
    Amplitude of Low Frequency Fluctuations (ALFF; Zang et al., 2007) and
    fractional Amplitude of Low Frequency Fluctuations (f/ALFF; Zou et al., 2008)
    are related measures that quantify the amplitude of low frequency
    oscillations (LFOs).  This function outputs ALFF and fALFF for the input.

    x - input clean resting state fmri
    mask - mask over which to compute f/alff
    flo - low frequency, typically 0.01
    fhi - high frequency, typically 0.1
    nuisance - optional nuisance matrix

    return dictionary with ALFF and fALFF images
    """
    xmat = ants.timeseries_to_matrix( x, mask )
    if nuisance is not None:
        xmat = ants.regress_components( xmat, nuisance )
    alffvec = xmat[0,:]*0
    falffvec = xmat[0,:]*0
    mytr = ants.get_spacing( x )[3]
    for n in range( xmat.shape[1] ):
        temp = alffmap( xmat[:,n], flo=flo, fhi=fhi, tr=mytr )
        alffvec[n]=temp['alff']
        falffvec[n]=temp['falff']
    alffi=ants.make_image( mask, alffvec )
    falffi=ants.make_image( mask, falffvec )
    alfftrimmedmean = calculate_trimmed_mean( alffvec, 0.01 )
    falfftrimmedmean = calculate_trimmed_mean( falffvec, 0.01 )
    alffi=alffi / alfftrimmedmean
    falffi=falffi / falfftrimmedmean
    return {  'alff': alffi, 'falff': falffi }




# augment_image - 8 lines
def augment_image( x,  max_rot=10, nzsd=1 ):
    rRotGenerator = ants.contrib.RandomRotate3D( ( max_rot*(-1.0), max_rot ), reference=x )
    tx = rRotGenerator.transform()
    itx = ants.invert_ants_transform(tx)
    y = ants.apply_ants_transform_to_image( tx, x, x, interpolation='linear')
    y = ants.add_noise_to_image( y,'additivegaussian', [0,nzsd] )
    return y, tx, itx



# boot_wmh - 44 lines
def boot_wmh( flair, t1, t1seg, mmfromconvexhull = 0.0, strict=True,
        probability_mask=None, prior_probability=None, n_simulations=16,
        random_seed = 42,
        verbose=False ) :
    import random
    random.seed( random_seed )
    if verbose and prior_probability is None:
        print("augmented flair")
    if verbose and prior_probability is not None:
        print("augmented flair with prior")
    wmh_sum_aug = 0
    wmh_sum_prior_aug = 0
    augprob = flair * 0.0
    augprob_prior = None
    if prior_probability is not None:
        augprob_prior = flair * 0.0
    for n in range(n_simulations):
        augflair, tx, itx = augment_image( ants.iMath(flair,"Normalize"), 5, 0.01 )
        locwmh = wmh( augflair, t1, t1seg, mmfromconvexhull = mmfromconvexhull,
            strict=strict, probability_mask=None, prior_probability=prior_probability )
        if verbose:
            print( "flair sim: " + str(n) + " vol: " + str( locwmh['wmh_mass'] )+ " vol-prior: " + str( locwmh['wmh_mass_prior'] )+ " snr: " + str( locwmh['wmh_SNR'] ) )
        wmh_sum_aug = wmh_sum_aug + locwmh['wmh_mass']
        wmh_sum_prior_aug = wmh_sum_prior_aug + locwmh['wmh_mass_prior']
        temp = locwmh['WMH_probability_map']
        augprob = augprob + ants.apply_ants_transform_to_image( itx, temp, flair, interpolation='linear')
        if prior_probability is not None:
            temp = locwmh['WMH_posterior_probability_map']
            augprob_prior = augprob_prior + ants.apply_ants_transform_to_image( itx, temp, flair, interpolation='linear')
    augprob = augprob * (1.0/float( n_simulations ))
    if prior_probability is not None:
        augprob_prior = augprob_prior * (1.0/float( n_simulations ))
    wmh_sum_aug = wmh_sum_aug / float( n_simulations )
    wmh_sum_prior_aug = wmh_sum_prior_aug / float( n_simulations )
    return{
      'flair' : ants.iMath(flair,"Normalize"),
      'WMH_probability_map' : augprob,
      'WMH_posterior_probability_map' : augprob_prior,
      'wmh_mass': wmh_sum_aug,
      'wmh_mass_prior': wmh_sum_prior_aug,
      'wmh_evr': locwmh['wmh_evr'],
      'wmh_SNR': locwmh['wmh_SNR']  }




# wmh - 112 lines
def wmh( flair, t1, t1seg,
    mmfromconvexhull = 3.0,
    strict=True,
    probability_mask=None,
    prior_probability=None,
    model='sysu',
    verbose=False ) :
    """
    Outputs the WMH probability mask and a summary single measurement

    Arguments
    ---------
    flair : ANTsImage
        input 3-D FLAIR brain image (not skull-stripped).

    t1 : ANTsImage
        input 3-D T1 brain image (not skull-stripped).

    t1seg : ANTsImage
        T1 segmentation image

    mmfromconvexhull : float
        restrict WMH to regions that are WM or mmfromconvexhull mm away from the
        convex hull of the cerebrum.   we choose a default value based on
        Figure 4 from:
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6240579/pdf/fnagi-10-00339.pdf

    strict: boolean - if True, only use convex hull distance

    probability_mask : None - use to compute wmh just once - then this function
        just does refinement and summary

    prior_probability : optional prior probability image in space of the input t1

    model : either sysu or hyper

    verbose : boolean

    Returns
    ---------
    WMH probability map and a summary single measurement which is the sum of the WMH map

    """
    import numpy as np
    import math
    t1_2_flair_reg = ants.registration(flair, t1, type_of_transform = 'antsRegistrationSyNRepro[r]') # Register T1 to Flair
    if probability_mask is None and model == 'sysu':
        if verbose:
            print('sysu')
        probability_mask = antspynet.sysu_media_wmh_segmentation( flair )
    elif probability_mask is None and model == 'hyper':
        if verbose:
            print('hyper')
        probability_mask = antspynet.hypermapp3r_segmentation( t1_2_flair_reg['warpedmovout'], flair )
    # t1_2_flair_reg = tra_initializer( flair, t1, n_simulations=4, max_rotation=5, transform=['rigid'], verbose=False )
    prior_probability_flair = None
    if prior_probability is not None:
        prior_probability_flair = ants.apply_transforms( flair, prior_probability,
            t1_2_flair_reg['fwdtransforms'] )
    wmseg_mask = ants.threshold_image( t1seg,
        low_thresh = 3, high_thresh = 3).iMath("FillHoles")
    wmseg_mask_use = ants.image_clone( wmseg_mask )
    distmask = None
    if mmfromconvexhull > 0:
            convexhull = ants.threshold_image( t1seg, 1, 4 )
            spc2vox = np.prod( ants.get_spacing( t1seg ) )
            voxdist = 0.0
            myspc = ants.get_spacing( t1seg )
            for k in range( t1seg.dimension ):
                voxdist = voxdist + myspc[k] * myspc[k]
            voxdist = math.sqrt( voxdist )
            nmorph = round( 2.0 / voxdist )
            convexhull = ants.morphology( convexhull, "close", nmorph ).iMath("FillHoles")
            dist = ants.iMath( convexhull, "MaurerDistance" ) * -1.0
            distmask = ants.threshold_image( dist, mmfromconvexhull, 1.e80 )
            wmseg_mask = wmseg_mask + distmask
            if strict:
                wmseg_mask_use = ants.threshold_image( wmseg_mask, 2, 2 )
            else:
                wmseg_mask_use = ants.threshold_image( wmseg_mask, 1, 2 )
    ##############################################################################
    wmseg_2_flair = ants.apply_transforms(flair, wmseg_mask_use,
        transformlist = t1_2_flair_reg['fwdtransforms'],
        interpolator = 'nearestNeighbor' )
    seg_2_flair = ants.apply_transforms(flair, t1seg,
        transformlist = t1_2_flair_reg['fwdtransforms'],
        interpolator = 'nearestNeighbor' )
    csfmask = ants.threshold_image(seg_2_flair,1,1)
    flairsnr = mask_snr( flair, csfmask, wmseg_2_flair, bias_correct = False )
    probability_mask_WM = wmseg_2_flair * probability_mask # Remove WMH signal outside of WM
    wmh_sum = np.prod( ants.get_spacing( flair ) ) * probability_mask_WM.sum()
    wmh_sum_prior = math.nan
    probability_mask_posterior = None
    if prior_probability_flair is not None:
        probability_mask_posterior = prior_probability_flair * probability_mask # use prior
        wmh_sum_prior = np.prod( ants.get_spacing(flair) ) * probability_mask_posterior.sum()
    if math.isnan( wmh_sum ):
        wmh_sum=0
    if math.isnan( wmh_sum_prior ):
        wmh_sum_prior=0
    flair_evr = antspyt1w.patch_eigenvalue_ratio( flair, 512, [16,16,16], evdepth = 0.9, mask=wmseg_2_flair )
    return{
        'WMH_probability_map_raw': probability_mask,
        'WMH_probability_map' : probability_mask_WM,
        'WMH_posterior_probability_map' : probability_mask_posterior,
        'wmh_mass': wmh_sum,
        'wmh_mass_prior': wmh_sum_prior,
        'wmh_evr' : flair_evr,
        'wmh_SNR' : flairsnr,
        'convexhull_mask': distmask }



