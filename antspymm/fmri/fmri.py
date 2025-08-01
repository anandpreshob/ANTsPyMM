"""
Fmri functions for ANTsPyMM
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

# resting_state_fmri_networks
def resting_state_fmri_networks( fmri, fmri_template, t1, t1segmentation,
    f=[0.03, 0.08],
    FD_threshold=5.0,
    spa = None,
    spt = None,
    nc = 5,
    outlier_threshold=0.250,
    ica_components = 0,
    impute = True,
    censor = True,
    despike = 2.5,
    motion_as_nuisance = True,
    powers = False,
    upsample = 3.0,
    clean_tmp = None,
    paramset='unset',
    verbose=False ):
  """
  Compute resting state network correlation maps based on the J Power labels.
  This will output a map for each of the major network systems.  This function 
  will by optionally upsample data to 2mm during the registration process if data 
  is below that resolution.

  registration - despike - anatomy - smooth - nuisance - bandpass - regress.nuisance - censor - falff - correlations

  Arguments
  ---------
  fmri : BOLD fmri antsImage

  fmri_template : reference space for BOLD

  t1 : ANTsImage
    input 3-D T1 brain image (brain extracted)

  t1segmentation : ANTsImage
    t1 segmentation - a six tissue segmentation image in T1 space

  f : band pass limits for frequency filtering; we use high-pass here as per Shirer 2015

  spa : gaussian smoothing for spatial component (physical coordinates)

  spt : gaussian smoothing for temporal component

  nc  : number of components for compcor filtering; if less than 1 we estimate on the fly based on explained variance; 10 wrt Shirer 2015 5 from csf and 5 from wm

  ica_components : integer if greater than 0 then include ica components

  impute : boolean if True, then use imputation in f/ALFF, PerAF calculation

  censor : boolean if True, then use censoring (censoring)

  despike : if this is greater than zero will run voxel-wise despiking in the 3dDespike (afni) sense; after motion-correction

  motion_as_nuisance: boolean will add motion and first derivative of motion as nuisance

  powers : boolean if True use Powers nodes otherwise 2023 Yeo 500 homotopic nodes (10.1016/j.neuroimage.2023.120010)

  upsample : float optionally isotropically upsample data to upsample (the parameter value) in mm during the registration process if data is below that resolution; if the input spacing is less than that provided by the user, the data will simply be resampled to isotropic resolution

  clean_tmp : will automatically try to clean the tmp directory - not recommended but can be used in distributed computing systems to help prevent failures due to accumulation of tmp files when doing large-scale processing.  if this is set, the float value clean_tmp will be interpreted as the age in hours of files to be cleaned.

  verbose : boolean

  Returns
  ---------
  a dictionary containing the derived network maps

  References
  ---------

  10.1162/netn_a_00071 "Methods that included global signal regression were the most consistently effective de-noising strategies."

  10.1016/j.neuroimage.2019.116157 "frontal and default model networks are most reliable whereas subcortical neteworks are least reliable"  "the most comprehensive studies of pipeline effects on edge-level reliability have been done by shirer (2015) and Parkes (2018)" "slice timing correction has minimal impact" "use of low-pass or narrow filter (discarding  high frequency information) reduced both reliability and signal-noise separation"

  10.1016/j.neuroimage.2017.12.073: Our results indicate that (1) simple linear regression of regional fMRI time series against head motion parameters and WM/CSF signals (with or without expansion terms) is not sufficient to remove head motion artefacts; (2) aCompCor pipelines may only be viable in low-motion data; (3) volume censoring performs well at minimising motion-related artefact but a major benefit of this approach derives from the exclusion of high-motion individuals; (4) while not as effective as volume censoring, ICA-AROMA performed well across our benchmarks for relatively low cost in terms of data loss; (5) the addition of global signal regression improved the performance of nearly all pipelines on most benchmarks, but exacerbated the distance-dependence of correlations between motion and functional connec- tivity; and (6) group comparisons in functional connectivity between healthy controls and schizophrenia patients are highly dependent on preprocessing strategy. We offer some recommendations for best practice and outline simple analyses to facilitate transparent reporting of the degree to which a given set of findings may be affected by motion-related artefact.

  10.1016/j.dcn.2022.101087 : We found that: 1) the most efficacious pipeline for both noise removal and information recovery included censoring, GSR, bandpass filtering, and head motion parameter (HMP) regression, 2) ICA-AROMA performed similarly to HMP regression and did not obviate the need for censoring, 3) GSR had a minimal impact on connectome fingerprinting but improved ISC, and 4) the strictest censoring approaches reduced motion correlated edges but negatively impacted identifiability.

  """

  import warnings

  if clean_tmp is not None:
    clean_tmp_directory( age_hours = clean_tmp )

  if nc > 1:
    nc = int(nc)
  else:
    nc=float(nc)

  type_of_transform="antsRegistrationSyNQuickRepro[r]" # , # should probably not change this
  remove_it=True
  output_directory = tempfile.mkdtemp()
  output_directory_w = output_directory + "/ts_t1_reg/"
  os.makedirs(output_directory_w,exist_ok=True)
  ofnt1tx = tempfile.NamedTemporaryFile(delete=False,suffix='t1_deformation',dir=output_directory_w).name

  import numpy as np
# Assuming core and utils are modules or packages with necessary functions

  if upsample > 0.0:
      spc = ants.get_spacing( fmri )
      minspc = upsample
      if min(spc[0:3]) < minspc:
          minspc = min(spc[0:3])
      newspc = [minspc,minspc,minspc]
      fmri_template = ants.resample_image( fmri_template, newspc, interp_type=0 )

  def temporal_derivative_same_shape(array):
    """
    Compute the temporal derivative of a 2D numpy array along the 0th axis (time)
    and ensure the output has the same shape as the input.

    :param array: 2D numpy array with time as the 0th axis.
    :return: 2D numpy array of the temporal derivative with the same shape as input.
    """
    derivative = np.diff(array, axis=0)
    
    # Append a row to maintain the same shape
    # You can choose to append a row of zeros or the last row of the derivative
    # Here, a row of zeros is appended
    zeros_row = np.zeros((1, array.shape[1]))
    return np.vstack((zeros_row, derivative ))

  def compute_tSTD(M, quantile, x=0, axis=0):
    stdM = np.std(M, axis=axis)
    # set bad values to x
    stdM[stdM == 0] = x
    stdM[np.isnan(stdM)] = x
    tt = round(quantile * 100)
    threshold_std = np.percentile(stdM, tt)
    return {'tSTD': stdM, 'threshold_std': threshold_std}

  def get_compcor_matrix(boldImage, mask, quantile):
    """
    Compute the compcor matrix.

    :param boldImage: The bold image.
    :param mask: The mask to apply, if None, it will be computed.
    :param quantile: Quantile for computing threshold in tSTD.
    :return: The compor matrix.
    """
    if mask is None:
        temp = ants.slice_image(boldImage, axis=boldImage.dimension - 1, idx=0)
        mask = ants.get_mask(temp)

    imagematrix = ants.timeseries_to_matrix(boldImage, mask)
    temp = compute_tSTD(imagematrix, quantile, 0)
    tsnrmask = ants.make_image(mask, temp['tSTD'])
    tsnrmask = ants.threshold_image(tsnrmask, temp['threshold_std'], temp['tSTD'].max())
    M = ants.timeseries_to_matrix(boldImage, tsnrmask)
    return M


  from sklearn.decomposition import FastICA
  def find_indices(lst, value):
    return [index for index, element in enumerate(lst) if element > value]

  def mean_of_list(lst):
    if not lst:  # Check if the list is not empty
        return 0  # Return 0 or appropriate value for an empty list
    return sum(lst) / len(lst)
  fmrispc = list( ants.get_spacing( fmri ) )
  if spa is None:
    spa = mean_of_list( fmrispc[0:3] ) * 1.0
  if spt is None:
    spt = fmrispc[3] * 0.5
      
  import numpy as np
  import pandas as pd
  import re
  import math
  # point data resources
  A = np.zeros((1,1))
  dfnname='DefaultMode'
  if powers:
      powers_areal_mni_itk = pd.read_csv( get_data('powers_mni_itk', target_extension=".csv")) # power coordinates
      coords='powers'
  else:
      powers_areal_mni_itk = pd.read_csv( get_data('ppmi_template_500Parcels_Yeo2011_17Networks_2023_homotopic', target_extension=".csv")) # yeo 2023 coordinates
      coords='yeo_17_500_2023'
  fmri = ants.iMath( fmri, 'Normalize' )
  bmask = antspynet.brain_extraction( fmri_template, 'bold' ).threshold_image(0.5,1).iMath("FillHoles")
  if verbose:
      print("Begin rsfmri motion correction")
  debug=False
  if debug:
      ants.image_write( fmri_template, '/tmp/fmri_template.nii.gz' )
      ants.image_write( fmri, '/tmp/fmri.nii.gz' )
      print("debug wrote fmri and fmri_template")
  # mot-co
  corrmo = timeseries_reg(
    fmri, fmri_template,
    type_of_transform=type_of_transform,
    total_sigma=0.5,
    fdOffset=2.0,
    trim = 8,
    output_directory=None,
    verbose=verbose,
    syn_metric='CC',
    syn_sampling=2,
    reg_iterations=[40,20,5],
    return_numpy_motion_parameters=True )
  
  if verbose:
      print("End rsfmri motion correction")
      print("--maximum motion : " + str(corrmo['FD'].max()) )
      print("=== next anatomically based mapping ===")

  despiking_count = np.zeros( corrmo['motion_corrected'].shape[3] )
  if despike > 0.0:
      corrmo['motion_corrected'], despiking_count = despike_time_series_afni( corrmo['motion_corrected'], c1=despike )

  despiking_count_summary = despiking_count.sum() / np.prod( corrmo['motion_corrected'].shape )
  high_motion_count=(corrmo['FD'] > FD_threshold ).sum()
  high_motion_pct=high_motion_count / fmri.shape[3]

  # filter mask based on TSNR
  mytsnr = tsnr( corrmo['motion_corrected'], bmask )
  mytsnrThresh = np.quantile( mytsnr.numpy(), 0.995 )
  tsnrmask = ants.threshold_image( mytsnr, 0, mytsnrThresh ).morphology("close",2)
  bmask = bmask * tsnrmask

  # anatomical mapping
  und = fmri_template * bmask
  t1reg = ants.registration( und, t1,
     "antsRegistrationSyNQuickRepro[s]", outprefix=ofnt1tx )
  if verbose:
    print("t1 2 bold done")
  gmseg = ants.threshold_image( t1segmentation, 2, 2 )
  gmseg = gmseg + ants.threshold_image( t1segmentation, 4, 4 )
  gmseg = ants.threshold_image( gmseg, 1, 4 )
  gmseg = ants.iMath( gmseg, 'MD', 1 ) # FIXMERSF
  gmseg = ants.apply_transforms( und, gmseg,
    t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' ) * bmask
  csfAndWM = ( ants.threshold_image( t1segmentation, 1, 1 ) +
               ants.threshold_image( t1segmentation, 3, 3 ) ).morphology("erode",1)
  csfAndWM = ants.apply_transforms( und, csfAndWM,
    t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  csf = ants.threshold_image( t1segmentation, 1, 1 )
  csf = ants.apply_transforms( und, csf, t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  wm = ants.threshold_image( t1segmentation, 3, 3 ).morphology("erode",1)
  wm = ants.apply_transforms( und, wm, t1reg['fwdtransforms'], interpolator = 'nearestNeighbor' )  * bmask
  if powers:
    ch2 = mm_read( ants.get_ants_data( "ch2" ) )
  else:
    ch2 = mm_read( get_data( "PPMI_template0_brain", target_extension='.nii.gz' ) )
  treg = ants.registration( 
    # this is to make the impact of resolution consistent
    ants.resample_image(t1, [1.0,1.0,1.0], interp_type=0), 
    ch2, "antsRegistrationSyNQuickRepro[s]" )
  if powers:
    concatx2 = treg['invtransforms'] + t1reg['invtransforms']
    pts2bold = ants.apply_transforms_to_points( 3, powers_areal_mni_itk, concatx2,
        whichtoinvert = ( True, False, True, False ) )
    locations = pts2bold.iloc[:,:3].values
    ptImg = ants.make_points_image( locations, bmask, radius = 2 )
  else:
    concatx2 = t1reg['fwdtransforms'] + treg['fwdtransforms']    
    rsfsegfn = get_data('ppmi_template_500Parcels_Yeo2011_17Networks_2023_homotopic', target_extension=".nii.gz")
    rsfsegimg = ants.image_read( rsfsegfn )
    ptImg = ants.apply_transforms( und, rsfsegimg, concatx2, interpolator='nearestNeighbor' ) * bmask
    pts2bold = powers_areal_mni_itk
    # ants.plot( und, ptImg, crop=True, axis=2 )

  # optional smoothing
  tr = ants.get_spacing( corrmo['motion_corrected'] )[3]
  smth = ( spa, spa, spa, spt ) # this is for sigmaInPhysicalCoordinates = TRUE
  simg = ants.smooth_image( corrmo['motion_corrected'], smth, sigma_in_physical_coordinates = True )

  # collect censoring indices
  hlinds = find_indices( corrmo['FD'], FD_threshold )
  if verbose:
    print("high motion indices")
    print( hlinds )
  if outlier_threshold < 1.0 and outlier_threshold > 0.0:
    fmrimotcorr, hlinds2 = loop_timeseries_censoring( corrmo['motion_corrected'], 
      threshold=outlier_threshold, verbose=verbose )
    hlinds.extend( hlinds2 )
    del fmrimotcorr
  hlinds = list(set(hlinds)) # make unique

  # nuisance
  globalmat = ants.timeseries_to_matrix( corrmo['motion_corrected'], bmask )
  globalsignal = np.nanmean( globalmat, axis = 1 )
  del globalmat
  compcorquantile=0.50
  nc_wm=nc_csf=nc
  if nc < 1:
    globalmat = get_compcor_matrix( corrmo['motion_corrected'], wm, compcorquantile )
    nc_wm = int(estimate_optimal_pca_components( data=globalmat, variance_threshold=nc))
    globalmat = get_compcor_matrix( corrmo['motion_corrected'], csf, compcorquantile )
    nc_csf = int(estimate_optimal_pca_components( data=globalmat, variance_threshold=nc))
    del globalmat
  if verbose:
    print("include compcor components as nuisance: csf " + str(nc_csf) + " wm " + str(nc_wm))
  mycompcor_csf = ants.compcor( corrmo['motion_corrected'],
    ncompcor=nc_csf, quantile=compcorquantile, mask = csf,
    filter_type='polynomial', degree=2 )
  mycompcor_wm = ants.compcor( corrmo['motion_corrected'],
    ncompcor=nc_wm, quantile=compcorquantile, mask = wm,
    filter_type='polynomial', degree=2 )
  nuisance = np.c_[ mycompcor_csf[ 'components' ], mycompcor_wm[ 'components' ] ]

  if motion_as_nuisance:
      if verbose:
          print("include motion as nuisance")
          print( corrmo['motion_parameters'].shape )
      deriv = temporal_derivative_same_shape( corrmo['motion_parameters']  )
      nuisance = np.c_[ nuisance, corrmo['motion_parameters'], deriv ]

  if ica_components > 0:
    if verbose:
        print("include ica components as nuisance: " + str(ica_components))
    ica = FastICA(n_components=ica_components, max_iter=10000, tol=0.001, random_state=42 )
    globalmat = ants.timeseries_to_matrix( corrmo['motion_corrected'], csfAndWM )
    nuisance_ica = ica.fit_transform(globalmat)  # Reconstruct signals
    nuisance = np.c_[ nuisance, nuisance_ica ]
    del globalmat

  # concat all nuisance data
  # nuisance = np.c_[ nuisance, mycompcor['basis'] ]
  # nuisance = np.c_[ nuisance, corrmo['FD'] ]
  nuisance = np.c_[ nuisance, globalsignal ]

  if impute:
    simgimp = impute_timeseries( simg, hlinds, method='linear')
  else:
    simgimp = simg

  # falff/alff stuff  def alff_image( x, mask, flo=0.01, fhi=0.1, nuisance=None ):
  myfalff=alff_image( simgimp, bmask, flo=f[0], fhi=f[1], nuisance=nuisance  )

  # bandpass any data collected before here -- if bandpass requested
  if f[0] > 0 and f[1] < 1.0:
    if verbose:
        print( "bandpass: " + str(f[0]) + " <=> " + str( f[1] ) )
    nuisance = ants.bandpass_filter_matrix( nuisance, tr = tr, lowf=f[0], highf=f[1] ) # some would argue against this
    globalmat = ants.timeseries_to_matrix( simg, bmask )
    globalmat = ants.bandpass_filter_matrix( globalmat, tr = tr, lowf=f[0], highf=f[1] ) # some would argue against this
    simg = ants.matrix_to_timeseries( simg, globalmat, bmask )

  if verbose:
    print("now regress nuisance")


  if len( hlinds ) > 0 :
    if censor:
        nuisance = remove_elements_from_numpy_array( nuisance, hlinds  )
        simg = remove_volumes_from_timeseries( simg, hlinds )

  gmmat = ants.timeseries_to_matrix( simg, bmask )
  gmmat = ants.regress_components( gmmat, nuisance )
  simg = ants.matrix_to_timeseries(simg, gmmat, bmask)


  # structure the output data
  outdict = {}
  outdict['paramset'] = paramset
  outdict['upsampling'] = upsample
  outdict['coords'] = coords
  outdict['dfnname']=dfnname
  outdict['meanBold'] = und

  # add correlation matrix that captures each node pair
  # some of the spheres overlap so extract separately from each ROI
  if powers:
    nPoints = int(pts2bold['ROI'].max())
    pointrange = list(range(int(nPoints)))
  else:
    nPoints = int(ptImg.max())
    pointrange = list(range(int(nPoints)))
  nVolumes = simg.shape[3]
  meanROI = np.zeros([nVolumes, nPoints])
  roiNames = []
  if debug:
      ptImgAll = und * 0.
  for i in pointrange:
    # specify name for matrix entries that's links back to ROI number and network; e.g., ROI1_Uncertain
    netLabel = re.sub( " ", "", pts2bold.loc[i,'SystemName'])
    netLabel = re.sub( "-", "", netLabel )
    netLabel = re.sub( "/", "", netLabel )
    roiLabel = "ROI" + str(pts2bold.loc[i,'ROI']) + '_' + netLabel
    roiNames.append( roiLabel )
    if powers:
        ptImage = ants.make_points_image(pts2bold.iloc[[i],:3].values, bmask, radius=1).threshold_image( 1, 1e9 )
    else:
        #print("Doing " + pts2bold.loc[i,'SystemName'] + " at " + str(i) )
        #ptImage = ants.mask_image( ptImg, ptImg, level=pts2bold['ROI'][pts2bold['SystemName']==pts2bold.loc[i,'SystemName']],binarize=True)
        ptImage=ants.threshold_image( ptImg, pts2bold.loc[i,'ROI'], pts2bold.loc[i,'ROI'] )
    if debug:
      ptImgAll = ptImgAll + ptImage
    if ptImage.sum() > 0 :
        meanROI[:,i] = ants.timeseries_to_matrix( simg, ptImage).mean(axis=1)

  if debug:
      ants.image_write( simg, '/tmp/simg.nii.gz' )
      ants.image_write( ptImgAll, '/tmp/ptImgAll.nii.gz' )
      ants.image_write( und, '/tmp/und.nii.gz' )
      ants.image_write( und, '/tmp/und.nii.gz' )

  # get full correlation matrix
  corMat = np.corrcoef(meanROI, rowvar=False)
  outputMat = pd.DataFrame(corMat)
  outputMat.columns = roiNames
  outputMat['ROIs'] = roiNames
  # add to dictionary
  outdict['fullCorrMat'] = outputMat

  networks = powers_areal_mni_itk['SystemName'].unique()
  # this is just for human readability - reminds us of which we choose by default
  if powers:
    netnames = ['Cingulo-opercular Task Control', 'Default Mode',
                    'Memory Retrieval', 'Ventral Attention', 'Visual',
                    'Fronto-parietal Task Control', 'Salience', 'Subcortical',
                    'Dorsal Attention']
    numofnets = [3,5,6,7,8,9,10,11,13]
  else:
    netnames = networks
    numofnets = list(range(len(netnames)))
 
  ct = 0
  for mynet in numofnets:
    netname = re.sub( " ", "", networks[mynet] )
    netname = re.sub( "-", "", netname )
    ww = np.where( powers_areal_mni_itk['SystemName'] == networks[mynet] )[0]
    if powers:
        dfnImg = ants.make_points_image(pts2bold.iloc[ww,:3].values, bmask, radius=1).threshold_image( 1, 1e9 )
    else:
        dfnImg = ants.mask_image( ptImg, ptImg, level=pts2bold['ROI'][pts2bold['SystemName']==networks[mynet]],binarize=True)
    if dfnImg.max() >= 1:
        if verbose:
            print("DO: " + coords + " " + netname )
        dfnmat = ants.timeseries_to_matrix( simg, ants.threshold_image( dfnImg, 1, dfnImg.max() ) )
        dfnsignal = np.nanmean( dfnmat, axis = 1 )
        nan_count_dfn = np.count_nonzero( np.isnan( dfnsignal) )
        if nan_count_dfn > 0 :
            warnings.warn( " mynet " + netnames[ mynet ] + " vs " +  " mean-signal has nans " + str( nan_count_dfn ) ) 
        gmmatDFNCorr = np.zeros( gmmat.shape[1] )
        if nan_count_dfn == 0:
            for k in range( gmmat.shape[1] ):
                nan_count_gm = np.count_nonzero( np.isnan( gmmat[:,k]) )
                if debug and False:
                    print( str( k ) +  " nans gm " + str(nan_count_gm)  )
                if nan_count_gm == 0:
                    gmmatDFNCorr[ k ] = pearsonr( dfnsignal, gmmat[:,k] )[0]
        corrImg = ants.make_image( bmask, gmmatDFNCorr  )
        outdict[ netname ] = corrImg * gmseg
    else:
        outdict[ netname ] = None
    ct = ct + 1

  A = np.zeros( ( len( numofnets ) , len( numofnets ) ) )
  A_wide = np.zeros( ( 1, len( numofnets ) * len( numofnets ) ) )
  newnames=[]
  newnames_wide=[]
  ct = 0
  for i in range( len( numofnets ) ):
      netnamei = re.sub( " ", "", networks[numofnets[i]] )
      netnamei = re.sub( "-", "", netnamei )
      newnames.append( netnamei  )
      ww = np.where( powers_areal_mni_itk['SystemName'] == networks[numofnets[i]] )[0]
      if powers:
          dfnImg = ants.make_points_image(pts2bold.iloc[ww,:3].values, bmask, radius=1).threshold_image( 1, 1e9 )
      else:
          dfnImg = ants.mask_image( ptImg, ptImg, level=pts2bold['ROI'][pts2bold['SystemName']==networks[numofnets[i]]],binarize=True)
      for j in range( len( numofnets ) ):
          netnamej = re.sub( " ", "", networks[numofnets[j]] )
          netnamej = re.sub( "-", "", netnamej )
          newnames_wide.append( netnamei + "_2_" + netnamej )
          A[i,j] = 0
          if dfnImg is not None and netnamej is not None:
            subbit = dfnImg == 1
            if subbit is not None:
                if subbit.sum() > 0 and netnamej in outdict:
                    A[i,j] = outdict[ netnamej ][ subbit ].mean()
          A_wide[0,ct] = A[i,j]
          ct=ct+1

  A = pd.DataFrame( A )
  A.columns = newnames
  A['networks']=newnames
  A_wide = pd.DataFrame( A_wide )
  A_wide.columns = newnames_wide
  outdict['corr'] = A
  outdict['corr_wide'] = A_wide
  outdict['fmri_template'] = fmri_template
  outdict['brainmask'] = bmask
  outdict['gmmask'] = gmseg
  outdict['alff'] = myfalff['alff']
  outdict['falff'] = myfalff['falff']
  # add global mean and standard deviation for post-hoc z-scoring
  outdict['alff_mean'] = (myfalff['alff'][myfalff['alff']!=0]).mean()
  outdict['alff_sd'] = (myfalff['alff'][myfalff['alff']!=0]).std()
  outdict['falff_mean'] = (myfalff['falff'][myfalff['falff']!=0]).mean()
  outdict['falff_sd'] = (myfalff['falff'][myfalff['falff']!=0]).std()

  perafimg = PerAF( simgimp, bmask )
  for k in pointrange:
    anatname=( pts2bold['AAL'][k] )
    if isinstance(anatname, str):
        anatname = re.sub("_","",anatname)
    else:
        anatname='Unk'
    if powers:
        kk = f"{k:0>3}"+"_"
    else:
        kk = f"{k % int(nPoints/2):0>3}"+"_"
    fname='falffPoint'+kk+anatname
    aname='alffPoint'+kk+anatname
    pname='perafPoint'+kk+anatname
    localsel = ptImg == k
    if localsel.sum() > 0 : # check if non-empty
        outdict[fname]=(outdict['falff'][localsel]).mean()
        outdict[aname]=(outdict['alff'][localsel]).mean()
        outdict[pname]=(perafimg[localsel]).mean()
    else:
        outdict[fname]=math.nan
        outdict[aname]=math.nan
        outdict[pname]=math.nan

  rsfNuisance = pd.DataFrame( nuisance )
  if remove_it:
    import shutil
    shutil.rmtree(output_directory, ignore_errors=True )

  if not powers:
    dfnsum=outdict['DefaultA']+outdict['DefaultB']+outdict['DefaultC']
    outdict['DefaultMode']=dfnsum
    dfnsum=outdict['VisCent']+outdict['VisPeri']
    outdict['Visual']=dfnsum

  nonbrainmask = ants.iMath( bmask, "MD",2) - bmask
  trimmask = ants.iMath( bmask, "ME",2)
  edgemask = ants.iMath( bmask, "ME",1) - trimmask
  outdict['motion_corrected'] = corrmo['motion_corrected']
  outdict['nuisance'] = rsfNuisance
  outdict['PerAF'] = perafimg
  outdict['tsnr'] = mytsnr
  outdict['ssnr'] = slice_snr( corrmo['motion_corrected'], csfAndWM, gmseg )
  outdict['dvars'] = dvars( corrmo['motion_corrected'], gmseg )
  outdict['bandpass_freq_0']=f[0]
  outdict['bandpass_freq_1']=f[1]
  outdict['censor']=int(censor)
  outdict['spatial_smoothing']=spa
  outdict['outlier_threshold']=outlier_threshold
  outdict['FD_threshold']=outlier_threshold
  outdict['high_motion_count'] = high_motion_count
  outdict['high_motion_pct'] = high_motion_pct
  outdict['despiking_count_summary'] = despiking_count_summary
  outdict['FD_max'] = corrmo['FD'].max()
  outdict['FD_mean'] = corrmo['FD'].mean()
  outdict['FD_sd'] = corrmo['FD'].std()
  outdict['bold_evr'] =  antspyt1w.patch_eigenvalue_ratio( und, 512, [16,16,16], evdepth = 0.9, mask = bmask )
  outdict['n_outliers'] = len(hlinds)
  outdict['nc_wm'] = int(nc_wm)
  outdict['nc_csf'] = int(nc_csf)
  outdict['minutes_original_data'] = ( tr * fmri.shape[3] ) / 60.0 # minutes of useful data
  outdict['minutes_censored_data'] = ( tr * simg.shape[3] ) / 60.0 # minutes of useful data
  return convert_np_in_dict( outdict )




# impute_timeseries
def impute_timeseries(time_series, volumes_to_impute, method='linear', verbose=False):
    """
    Impute specified volumes from a time series with interpolated values.

    :param time_series: ANTsImage representing the time series (4D image).
    :param volumes_to_impute: List of volume indices to impute.
    :param method: Interpolation method ('linear' or other methods if implemented).
    :param verbose: boolean
    :return: ANTsImage with specified volumes imputed.
    """
    if not isinstance(time_series, ants.core.ants_image.ANTsImage):
        raise ValueError("time_series must be an ANTsImage.")

    if time_series.dimension != 4:
        raise ValueError("time_series must be a 4D image.")

    # Convert time_series to numpy for manipulation
    time_series_np = time_series.numpy()
    total_volumes = time_series_np.shape[3]

    # Create a complement list of volumes not to impute
    volumes_not_to_impute = [i for i in range(total_volumes) if i not in volumes_to_impute]

    # Define the lower and upper bounds
    min_valid_index = min(volumes_not_to_impute)
    max_valid_index = max(volumes_not_to_impute)

    for vol_idx in volumes_to_impute:
        # Ensure the volume index is within the valid range
        if vol_idx < 0 or vol_idx >= total_volumes:
            raise ValueError(f"Volume index {vol_idx} is out of bounds.")

        # Find the nearest valid lower index within the bounds
        lower_candidates = [v for v in volumes_not_to_impute if v <= vol_idx]
        lower_idx = max(lower_candidates) if lower_candidates else min_valid_index

        # Find the nearest valid upper index within the bounds
        upper_candidates = [v for v in volumes_not_to_impute if v >= vol_idx]
        upper_idx = min(upper_candidates) if upper_candidates else max_valid_index

        if verbose:
            print(f"Imputing volume {vol_idx} using indices {lower_idx} and {upper_idx}")

        if method == 'linear':
            # Linear interpolation between the two nearest volumes
            lower_volume = time_series_np[..., lower_idx]
            upper_volume = time_series_np[..., upper_idx]
            interpolated_volume = (lower_volume + upper_volume) / 2
        else:
            # Placeholder for other interpolation methods
            raise NotImplementedError("Currently, only linear interpolation is implemented.")

        # Replace the specified volume with the interpolated volume
        time_series_np[..., vol_idx] = interpolated_volume

    # Convert the numpy array back to ANTsImage
    imputed_time_series = ants.from_numpy(time_series_np)
    imputed_time_series = ants.copy_image_info(time_series, imputed_time_series)

    return imputed_time_series



# score_fmri_censoring
def score_fmri_censoring(cbfts, csf_seg, gm_seg, wm_seg ):
    """
    Process CBF time series to remove high-leverage points.
    Derived from the SCORE algorithm by Sudipto Dolui et. al.

    Parameters:
    cbfts (ANTsImage): 4D ANTsImage of CBF time series.
    csf_seg (ANTsImage): CSF binary map.
    gm_seg (ANTsImage): Gray matter binary map.
    wm_seg (ANTsImage): WM binary map.

    Returns:
    ANTsImage: Processed CBF time series.
    ndarray: Index of removed volumes.
    """
    
    n_gm_voxels = np.sum(gm_seg.numpy()) - 1
    n_wm_voxels = np.sum(wm_seg.numpy()) - 1
    n_csf_voxels = np.sum(csf_seg.numpy()) - 1
    mask1img = gm_seg + wm_seg + csf_seg
    mask1 = (mask1img==1).numpy()
    
    cbfts_np = cbfts.numpy()
    gmbool = (gm_seg==1).numpy()
    csfbool = (csf_seg==1).numpy()
    wmbool = (wm_seg==1).numpy()
    gm_cbf_ts = ants.timeseries_to_matrix( cbfts, gm_seg )
    gm_cbf_ts = np.squeeze(np.mean(gm_cbf_ts, axis=1))
    
    median_gm_cbf = np.median(gm_cbf_ts)
    mad_gm_cbf = np.median(np.abs(gm_cbf_ts - median_gm_cbf)) / 0.675
    indx = np.abs(gm_cbf_ts - median_gm_cbf) > (2.5 * mad_gm_cbf)
    
    # the spatial mean
    spatmeannp = np.mean(cbfts_np[:, :, :, ~indx], axis=3)
    spatmean = ants.from_numpy( spatmeannp )
    V = (
        n_gm_voxels * np.var(spatmeannp[gmbool])
        + n_wm_voxels * np.var(spatmeannp[wmbool])
        + n_csf_voxels * np.var(spatmeannp[csfbool])
    )
    V1 = math.inf
    ct=0
    while V < V1:
        ct=ct+1
        V1 = V
        CC = np.zeros(cbfts_np.shape[3])
        for s in range(cbfts_np.shape[3]):
            if indx[s]:
                continue
            tmp1 = ants.from_numpy( cbfts_np[:, :, :, s] )
            CC[s] = ants.image_similarity( spatmean, tmp1, metric_type='Correlation', fixed_mask=mask1img )
        inx = np.argmin(CC)
        indx[inx] = True
        spatmeannp = np.mean(cbfts_np[:, :, :, ~indx], axis=3)
        spatmean = ants.from_numpy( spatmeannp )
        V = (
          n_gm_voxels * np.var(spatmeannp[gmbool]) + 
          n_wm_voxels * np.var(spatmeannp[wmbool]) + 
          n_csf_voxels * np.var(spatmeannp[csfbool])
        )
    cbfts_recon = cbfts_np[:, :, :, ~indx]
    cbfts_recon = np.nan_to_num(cbfts_recon)
    cbfts_recon_ants = ants.from_numpy(cbfts_recon)
    cbfts_recon_ants = ants.copy_image_info(cbfts, cbfts_recon_ants)
    return cbfts_recon_ants, indx



