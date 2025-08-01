"""
Utility functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# version - 26 lines
def version( ):
    """
    report versions of this package and primary dependencies

    Arguments
    ---------
    None

    Returns
    -------
    a dictionary with package name and versions

    Example
    -------
    >>> import antspymm
    >>> antspymm.version()
    """
    import pkg_resources
    return {
              'tensorflow': pkg_resources.get_distribution("tensorflow").version,
              'antspyx': pkg_resources.get_distribution("antspyx").version,
              'antspynet': pkg_resources.get_distribution("antspynet").version,
              'antspyt1w': pkg_resources.get_distribution("antspyt1w").version,
              'antspymm': pkg_resources.get_distribution("antspymm").version
              }



# check_pd_construction - 72 lines
    def check_pd_construction(data, columns):
        return all(len(row) == len(columns) for row in data)

    flair_filename.sort()
    rsf_filenames.sort()
    dti_filenames.sort()
    nm_filenames.sort()
    perf_filename.sort()

    valid_modalities = get_valid_modalities()  

    if not isinstance(t1_filename, str):
        raise ValueError("t1_filename is not a string")
    if not exists(t1_filename):
        raise ValueError("t1_filename does not exist")

    validate_modality(modality, valid_modalities)

    if not exists(source_image_directory):
        raise ValueError("source_image_directory does not exist")

    rsf_filenames = extend_list_to_length(rsf_filenames, 2)
    dti_filenames = extend_list_to_length(dti_filenames, 2)
    nm_filenames = extend_list_to_length(nm_filenames, 11)

    validate_filename(t1_filename, ["T1w"], "T1w is not in t1 filename " + t1_filename)

    if flair_filename:
        flair_filename = flair_filename[0] if isinstance(flair_filename, list) else flair_filename
        validate_filename(flair_filename, ["lair"], "flair is not in flair filename " + flair_filename)

    if perf_filename:
        perf_filename = perf_filename[0] if isinstance(perf_filename, list) else perf_filename
        validate_filename(perf_filename, ["perf"], "perf_filename is not a valid perfusion (perf) filename")

    for k in nm_filenames:
        if k: validate_filename(k, ["NM"], "NM is not in NM filename " + k)

    for k in dti_filenames:
        if k: validate_filename(k, ["DTI","dwi"], "DTI or dwi is not in DTI filename " + k)

    for k in rsf_filenames:
        if k: validate_filename(k, ["fMRI","func"], "rsfMRI or func is not in rsfMRI filename " + k)

    allfns = [t1_filename, flair_filename] + nm_filenames + dti_filenames + rsf_filenames + [perf_filename]
    for k in allfns:
        if k and not exists(k):
            raise ValueError("image " + k + " does not exist")

    coredata = [projectID, subjectID, date, imageUniqueID, modality,
                source_image_directory, output_image_directory, t1_filename, 
                flair_filename, perf_filename]
    mydata0 = coredata + rsf_filenames + dti_filenames
    mydata = mydata0 + nm_filenames

    corecols = ['projectID', 'subjectID', 'date', 'imageID', 'modality',
                'sourcedir', 'outputdir', 'filename', 'flairid', 'perfid']
    mycols0 = corecols + ['rsfid1', 'rsfid2', 'dtid1', 'dtid2']
    nmext = ['nmid1', 'nmid2', 'nmid3', 'nmid4', 'nmid5',
             'nmid6', 'nmid7', 'nmid8', 'nmid9', 'nmid10', 'nmid11']
    mycols = mycols0 + nmext

    if not check_pd_construction([mydata], mycols):
        print( mydata )
        print( mycols )
        raise ValueError("Error in generate_mm_dataframe: len(mycols) != len(mydata), indicating bad input parameters.")

    studycsv = pd.DataFrame([mydata], columns=mycols)
    return studycsv





# collect_blind_qc_by_modality - 30 lines
def collect_blind_qc_by_modality( modality_path, set_index_to_fn=True ):
    """
    Collects blind QC data from multiple CSV files with the same modality.

    Args:

    modality_path (str): The path to the folder containing the CSV files.

    set_index_to_fn: boolean

    Returns:
    Pandas DataFrame: A DataFrame containing all the blind QC data from the CSV files.
    """
    import glob as glob
    fns = glob.glob( modality_path )
    fns.sort()
    jdf = pd.DataFrame()
    for k in range(len(fns)):
        temp=pd.read_csv(fns[k])
        if not 'filename' in temp.keys():
            temp['filename']=fns[k]
        jdf=pd.concat( [jdf,temp], axis=0, ignore_index=False )
    if set_index_to_fn:
        jdf.reset_index(drop=True)
        if "Unnamed: 0" in jdf.columns:
            holder=jdf.pop( "Unnamed: 0" )
        jdf.set_index('filename')
    return jdf




# add_repeat_column - 21 lines
def add_repeat_column(df, groupby_column):
    """
    Adds a 'repeat' column to the DataFrame that counts occurrences of each unique value
    in the specified 'groupby_column'. The count increments from 1 for each identical entry.
    
    Parameters:
    - df: pandas DataFrame.
    - groupby_column: The name of the column to group by and count repeats.
    
    Returns:
    - Modified pandas DataFrame with an added 'repeat' column.
    """
    # Validate if the groupby_column exists in the DataFrame
    if groupby_column not in df.columns:
        raise ValueError(f"Column '{groupby_column}' does not exist in the DataFrame.")
    
    # Count the occurrences of each unique value in the specified column and increment from 1
    df['repeat'] = df.groupby(groupby_column).cumcount() + 1
    
    return df



# timeseries_n3 - 36 lines
def timeseries_n3(x):
    """
    Perform N3 bias field correction on a time-series image dataset using ANTsPy library.

    This function processes a multi-dimensional image dataset, where the last dimension
    represents different time points. It applies N3 bias field correction to each time point 
    individually to correct intensity non-uniformity.

    Parameters:
    x (ndarray): A multi-dimensional array where the last dimension represents time points. 
                 Each 'slice' along this dimension is a separate image to be corrected.

    Returns:
    ndarray: A multi-dimensional array of the same shape as x, with N3 bias field correction 
             applied to each time slice.

    The function works as follows:
    - Initializes an empty list `mimg` to store the corrected images.
    - Determines the number of time points in the input image series.
    - Iterates over each time point, extracting the image slice and applying N3 bias 
      field correction.
    - The corrected images are then appended to the `mimg` list.
    - Finally, the list of corrected images is converted back into a multi-dimensional 
      array and returned.

    Example:
    corrected_images = timeseries_n3(image_data)
    """
    mimg = []
    n = len(x.shape) - 1
    for kk in range(x.shape[n]):
        temp = ants.slice_image(x, axis=n, idx=kk)
        temp = ants.n3_bias_field_correction(temp, downsample_factor=2)
        mimg.append(temp)
    return ants.list_to_ndimage(x, mimg)



# getmtime - 19 lines
    def getmtime(x):
        x= dt.datetime.fromtimestamp(os.path.getmtime(x)).strftime("%Y-%m-%d %H:%M:%d")
        return x
    df=pd.DataFrame(columns=['filename','file_last_mod_t','else','sid','visitdate','modality','uid'])
    df.set_index('filename')
    df['filename'] = pd.Series([file for file in filename_list ])
    # I applied a time modified file to df['file_last_mod_t'] by getmtime function
    df['file_last_mod_t'] = df['filename'].apply(lambda x: getmtime(x))
    for k in range(df.shape[0]):
        locfn=df['filename'].iloc[k]
        splitter=os.path.basename(locfn).split( myseparator )
        df['sid'].iloc[k]=splitter[1]
        df['visitdate'].iloc[k]=splitter[2]
        df['modality'].iloc[k]=splitter[3]
        temp = os.path.splitext(splitter[4])[0]
        df['uid'].iloc[k]=os.path.splitext(temp)[0]
    return df




# copy_spatial_metadata_from_3d_to_4d - 44 lines
def copy_spatial_metadata_from_3d_to_4d(spatial_img, timeseries_img):
    """
    Copy spatial metadata (origin, spacing, direction) from a 3D image to the
    spatial dimensions (first 3) of a 4D image, preserving the 4th dimension's metadata.

    Parameters
    ----------
    spatial_img : ants.ANTsImage
        A 3D ANTsImage with the desired spatial metadata.
    timeseries_img : ants.ANTsImage
        A 4D ANTsImage to update.

    Returns
    -------
    ants.ANTsImage
        A 4D ANTsImage with updated spatial metadata.
    """
    if spatial_img.dimension != 3:
        raise ValueError("spatial_img must be a 3D ANTsImage.")
    if timeseries_img.dimension != 4:
        raise ValueError("timeseries_img must be a 4D ANTsImage.")
    # Get 3D metadata
    spatial_origin = list(spatial_img.origin)
    spatial_spacing = list(spatial_img.spacing)
    spatial_direction = spatial_img.direction  # 3x3
    # Get original 4D metadata
    ts_spacing = list(timeseries_img.spacing)
    ts_origin = list(timeseries_img.origin)
    ts_direction = timeseries_img.direction  # 4x4
    # Replace only the first 3 entries for origin and spacing
    new_origin = spatial_origin + [ts_origin[3]]
    new_spacing = spatial_spacing + [ts_spacing[3]]
    # Replace top-left 3x3 block of direction matrix, preserve last row/column
    new_direction = ts_direction.copy()
    new_direction[:3, :3] = spatial_direction
    # Create updated image
    updated_img = ants.from_numpy(
        timeseries_img.numpy(),
        origin=new_origin,
        spacing=new_spacing,
        direction=new_direction
    )
    return updated_img



# timeseries_transform - 40 lines
def timeseries_transform(transform, image, reference, interpolation='linear'):
    """
    Apply a spatial transform to each 3D volume in a 4D time series image.

    Parameters
    ----------
    transform : ants transform object
        Path(s) to ANTs-compatible transform(s) to apply.
    image : ants.ANTsImage
        4D input image with shape (X, Y, Z, T).
    reference : ants.ANTsImage
        Reference image to match in space.
    interpolation : str
        Interpolation method: 'linear', 'nearestNeighbor', etc.

    Returns
    -------
    ants.ANTsImage
        4D transformed image.
    """
    if image.dimension != 4:
        raise ValueError("Input image must be 4D (X, Y, Z, T).")
    n_volumes = image.shape[3]
    transformed_volumes = []
    for t in range(n_volumes):
        vol = ants.slice_image( image, 3, t )
        transformed = ants.apply_ants_transform_to_image(
            transform=transform,
            image=vol,
            reference=reference,
            interpolation=interpolation
        )
        transformed_volumes.append(transformed.numpy())
    # Stack along time axis and convert to ANTsImage
    transformed_array = np.stack(transformed_volumes, axis=-1)
    out_image = ants.from_numpy(transformed_array)
    out_image = ants.copy_image_info(image, out_image)
    out_image = copy_spatial_metadata_from_3d_to_4d(reference, out_image)
    return out_image



# map_scalar_to_labels - 24 lines
def map_scalar_to_labels(dataframe, label_image_template):
    """
    Map scalar values from a DataFrame to associated integer image labels.

    Parameters:
    - dataframe (pd.DataFrame): A Pandas DataFrame containing a label column and scalar_value column.
    - label_image_template (ants.ANTsImage): ANTs image with (at least some of) the same values as labels.

    Returns:
    - ants.ANTsImage: A label image with scalar values mapped to associated integer labels.
    """

    # Create an empty label image with the same geometry as the template
    mapped_label_image = label_image_template.clone() * 0.0

    # Loop through DataFrame and map scalar values to labels
    for index, row in dataframe.iterrows():
        label = int(row['label'])  # Assuming the DataFrame has a 'label' column
        scalar_value = row['scalar_value']  # Replace with your column name
        mapped_label_image[label_image_template == label] = scalar_value

    return mapped_label_image




# get_average_rsf - 31 lines
def get_average_rsf( x, min_t=10, max_t=35 ):
    """
    automatically generates the average bold image with quick registration

    returns:
        avg_bold
    """
    output_directory = tempfile.mkdtemp()
    ofn = output_directory + "/w"
    bavg = ants.slice_image( x, axis=3, idx=0 ) * 0.0
    oavg = ants.slice_image( x, axis=3, idx=0 )
    if x.shape[3] <= min_t:
        min_t=0
    if x.shape[3] <= max_t:
        max_t=x.shape[3]
    for myidx in range(min_t,max_t):
        b0 = ants.slice_image( x, axis=3, idx=myidx)
        bavg = bavg + ants.registration(oavg,b0,'antsRegistrationSyNRepro[r]',outprefix=ofn)['warpedmovout']
    bavg = ants.iMath( bavg, 'Normalize' )
    oavg = ants.image_clone( bavg )
    bavg = oavg * 0.0
    for myidx in range(min_t,max_t):
        b0 = ants.slice_image( x, axis=3, idx=myidx)
        bavg = bavg + ants.registration(oavg,b0,'antsRegistrationSyNRepro[r]',outprefix=ofn)['warpedmovout']
    import shutil
    shutil.rmtree(output_directory, ignore_errors=True )
    bavg = ants.iMath( bavg, 'Normalize' )
    return bavg
    # return ants.n4_bias_field_correction(bavg, mask=ants.get_mask( bavg ) )




# mc_denoise - 22 lines
def mc_denoise( x, ratio = 0.5 ):
    """
    ants denoising for timeseries (4D)

    Arguments
    ---------
    x : an antsImage 4D

    ratio : weight between 1 and 0 - lower weights bring result closer to initial image

    Returns
    -------
    denoised time series

    """
    dwpimage = []
    for myidx in range(x.shape[3]):
        b0 = ants.slice_image( x, axis=3, idx=myidx)
        dnzb0 = ants.denoise_image( b0, p=1,r=1,noise_model='Gaussian' )
        dwpimage.append( dnzb0 * ratio + b0 * (1.0-ratio) )
    return ants.list_to_ndimage( x, dwpimage )



# impute_fa - 16 lines
def impute_fa( fa, md ):
    """
    impute bad values in dti, fa, md
    """
    def imputeit( x, fa ):
        badfa=ants.threshold_image(fa,1,1)
        if badfa.max() == 1:
            temp=ants.image_clone(x)
            temp[badfa==1]=0
            temp=ants.iMath(temp,'GD',2)
            x[ badfa==1 ]=temp[badfa==1]
        return x
    md=imputeit( md, fa )
    fa=imputeit( ants.image_clone(fa), fa )
    return fa, md



# imputeit - 12 lines
    def imputeit( x, fa ):
        badfa=ants.threshold_image(fa,1,1)
        if badfa.max() == 1:
            temp=ants.image_clone(x)
            temp[badfa==1]=0
            temp=ants.iMath(temp,'GD',2)
            x[ badfa==1 ]=temp[badfa==1]
        return x
    md=imputeit( md, fa )
    fa=imputeit( ants.image_clone(fa), fa )
    return fa, md



# tra_initializer - 85 lines
def tra_initializer( fixed, moving, n_simulations=32, max_rotation=30,
    transform=['rigid'], compreg=None, random_seed=42, verbose=False ):
    """
    multi-start multi-transform registration solution - based on ants.registration

    fixed: fixed image

    moving: moving image

    n_simulations : number of simulations

    max_rotation : maximum rotation angle

    transform : list of transforms to loop through

    compreg : registration results against which to compare

    random_seed : random seed for reproducibility

    verbose : boolean

    """
    import random
    if random_seed is not None:
        random.seed(random_seed)
    if True:
        output_directory = tempfile.mkdtemp()
        output_directory_w = output_directory + "/tra_reg/"
        os.makedirs(output_directory_w,exist_ok=True)
        bestmi = math.inf
        bestvar = 0.0
        myorig = list(ants.get_origin( fixed ))
        mymax = 0;
        for k in range(len( myorig ) ):
            if abs(myorig[k]) > mymax:
                mymax = abs(myorig[k])
        maxtrans = mymax * 0.05
        if compreg is None:
            bestreg=ants.registration( fixed,moving,'Translation',
                outprefix=output_directory_w+"trans")
            initx = ants.read_transform( bestreg['fwdtransforms'][0] )
        else :
            bestreg=compreg
            initx = ants.read_transform( bestreg['fwdtransforms'][0] )
        for mytx in transform:
            regtx = 'antsRegistrationSyNRepro[r]'
            with tempfile.NamedTemporaryFile(suffix='.h5') as tp:
                if mytx == 'translation':
                    regtx = 'Translation'
                    rRotGenerator = ants.contrib.RandomTranslate3D( ( maxtrans*(-1.0), maxtrans ), reference=fixed )
                elif mytx == 'affine':
                    regtx = 'Affine'
                    rRotGenerator = ants.contrib.RandomRotate3D( ( maxtrans*(-1.0), maxtrans ), reference=fixed )
                else:
                    rRotGenerator = ants.contrib.RandomRotate3D( ( max_rotation*(-1.0), max_rotation ), reference=fixed )
                for k in range(n_simulations):
                    simtx = ants.compose_ants_transforms( [rRotGenerator.transform(), initx] )
                    ants.write_transform( simtx, tp.name )
                    if k > 0:
                        reg = ants.registration( fixed, moving, regtx,
                            initial_transform=tp.name,
                            outprefix=output_directory_w+"reg"+str(k),
                            verbose=False )
                    else:
                        reg = ants.registration( fixed, moving,
                            regtx,
                            outprefix=output_directory_w+"reg"+str(k),
                            verbose=False )
                    mymi = math.inf
                    temp = reg['warpedmovout']
                    myvar = temp.numpy().var()
                    if verbose:
                        print( str(k) + " : " + regtx  + " : " + mytx + " _var_ " + str( myvar ) )
                    if myvar > 0 :
                        mymi = ants.image_mutual_information( fixed, temp )
                        if mymi < bestmi:
                            if verbose:
                                print( "mi @ " + str(k) + " : " + str(mymi), flush=True)
                            bestmi = mymi
                            bestreg = reg
                            bestvar = myvar
        if bestvar == 0.0 and compreg is not None:
            return compreg        
        return bestreg



# compute_PerAF_voxel - 18 lines
def compute_PerAF_voxel(time_series):
    """
    Compute the Percentage Amplitude Fluctuation (PerAF) for a given time series.

    10.1371/journal.pone.0227021

    PerAF = 100/n * sum(|(x_i - m)/m|) 
    where m = 1/n * sum(x_i), x_i is the signal intensity at each time point, 
    and n is the total number of time points.

    :param time_series: Numpy array of time series data
    :return: Computed PerAF value
    """
    n = len(time_series)
    m = np.mean(time_series)
    perAF = 100 / n * np.sum(np.abs((time_series - m) / m))
    return perAF



# PerAF - 27 lines
def PerAF( x, mask, globalmean=True ):
    """
    Compute the Percentage Amplitude Fluctuation (PerAF) for a given time series.

    10.1371/journal.pone.0227021

    PerAF = 100/n * sum(|(x_i - m)/m|) 
    where m = 1/n * sum(x_i), x_i is the signal intensity at each time point, 
    and n is the total number of time points.

    :param x: time series antsImage
    :param mask: brain mask
    :param globalmean: boolean if True divide by the globalmean in the brain mask
    :return: Computed PerAF image
    """
    time_series = ants.timeseries_to_matrix( x, mask )
    n = time_series.shape[1]
    vec = np.zeros( n )
    for i in range(n):
        vec[i] = compute_PerAF_voxel( time_series[:,i] )
    outimg = ants.make_image( mask, vec )
    if globalmean:
        outimg = outimg / calculate_trimmed_mean( vec, 0.01 )
    return outimg





# l1_fit_polynomial - 46 lines
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



# replicate_list - 9 lines
  def replicate_list(user_list, target_size):
    # Calculate the number of times the list should be replicated
    replication_factor = target_size // len(user_list)
    # Replicate the list and handle any remaining elements
    replicated_list = user_list * replication_factor
    remaining_elements = target_size % len(user_list)
    replicated_list += user_list[:remaining_elements]
    return replicated_list



# warn_if_small_mask - 28 lines
def warn_if_small_mask( mask: ants.ANTsImage, threshold_fraction: float = 0.05, label: str = ' ' ):
    """
    Warn the user if the number of non-zero voxels in the mask
    is less than a given fraction of the total number of voxels in the mask.

    Parameters
    ----------
    mask : ants.ANTsImage
        The binary mask to evaluate.
    threshold_fraction : float, optional
        Fraction threshold below which a warning is triggered (default is 0.05).
    
    Returns
    -------
    None
    """
    import warnings
    image_size = np.prod(mask.shape)
    mask_size = np.count_nonzero(mask.numpy())
    if mask_size / image_size < threshold_fraction:
        percentage = 100.0 * mask_size / image_size
        warnings.warn(
            f"[ants] Warning: {label} contains only {mask_size} voxels "
            f"({percentage:.2f}% of image volume). "
            f"This is below the threshold of {threshold_fraction * 100:.2f}% and may lead to unreliable results.",
            UserWarning
        )



# select_regression_model - 24 lines
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



# replicate_list - 9 lines
  def replicate_list(user_list, target_size):
    # Calculate the number of times the list should be replicated
    replication_factor = target_size // len(user_list)
    # Replicate the list and handle any remaining elements
    replicated_list = user_list * replication_factor
    remaining_elements = target_size % len(user_list)
    replicated_list += user_list[:remaining_elements]
    return replicated_list



# makewideout - 6 lines
    def makewideout( x, separator = '-' ):
        return x + separator + 'mmwide.csv'
    if nrg_modality_list[0] != 'T1w':
        nrg_modality_list.insert(0, "T1w" )
    testloop = False
    counter=0


# makewideout - 4 lines
    def makewideout( x, separator = mysep ):
        return x + separator + 'mmwide.csv'
    testloop = False
    counter=0


# daniell_window_modified - 11 lines
    def daniell_window_modified(m):
        """ Single-pass modified Daniell kernel window.

        Weight is normalized to add up to 1, and all values are the same, other than the first and the
        last, which are divided by 2.
        """
        def w(k):
            return np.where(np.abs(k) < m, 1 / (2*m), np.where(np.abs(k) == m, 1/(4*m), 0))

        return w(np.arange(-m, m+1))



# w - 5 lines
        def w(k):
            return np.where(np.abs(k) < m, 1 / (2*m), np.where(np.abs(k) == m, 1/(4*m), 0))

        return w(np.arange(-m, m+1))



# down2iso - 25 lines
def down2iso( x, interpolation='linear', takemin=False ):
    """
    will downsample an anisotropic image to an isotropic resolution

    x: input image

    interpolation: linear or nearestneighbor

    takemin : boolean map to min space; otherwise max

    return image downsampled to isotropic resolution
    """
    spc = ants.get_spacing( x )
    if takemin:
        newspc = np.asarray(spc).min()
    else:
        newspc = np.asarray(spc).max()
    newspc = np.repeat( newspc, x.dimension )
    if interpolation == 'linear':
        xs = ants.resample_image( x, newspc, interp_type=0)
    else:
        xs = ants.resample_image( x, newspc, interp_type=1)
    return xs




# chunks - 6 lines
    def chunks(l, n):
        """Yield n number of sequential chunks from l."""
        d, r = divmod(len(l), n)
        for i in range(n):
            si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
            yield l[si:si+(d+1 if i < r else d)]


# get_names_from_data_frame - 33 lines
def get_names_from_data_frame(x, demogIn, exclusions=None):
    """
    data = {'Name':['Tom', 'nick', 'krish', 'jack'], 'Age':[20, 21, 19, 18]}
    antspymm.get_names_from_data_frame( ['e'], df )
    antspymm.get_names_from_data_frame( ['a','e'], df )
    antspymm.get_names_from_data_frame( ['e'], df, exclusions='N' )
    """
    # Check if x is a string and convert it to a list
    if isinstance(x, str):
        x = [x]
    def get_unique( qq ):
        unique = []
        for number in qq:
            if number in unique:
                continue
            else:
                unique.append(number)
        return unique
    outnames = list(demogIn.columns[demogIn.columns.str.contains(x[0])])
    if len(x) > 1:
        for y in x[1:]:
            outnames = [i for i in outnames if y in i]
    outnames = get_unique( outnames )
    if exclusions is not None:
        toexclude = [name for name in outnames if exclusions[0] in name ]
        if len(exclusions) > 1:
            for zz in exclusions[1:]:
                toexclude.extend([name for name in outnames if zz in name ])
        if len(toexclude) > 0:
            outnames = [name for name in outnames if name not in toexclude]
    return outnames




# get_unique - 23 lines
    def get_unique( qq ):
        unique = []
        for number in qq:
            if number in unique:
                continue
            else:
                unique.append(number)
        return unique
    outnames = list(demogIn.columns[demogIn.columns.str.contains(x[0])])
    if len(x) > 1:
        for y in x[1:]:
            outnames = [i for i in outnames if y in i]
    outnames = get_unique( outnames )
    if exclusions is not None:
        toexclude = [name for name in outnames if exclusions[0] in name ]
        if len(exclusions) > 1:
            for zz in exclusions[1:]:
                toexclude.extend([name for name in outnames if zz in name ])
        if len(toexclude) > 0:
            outnames = [name for name in outnames if name not in toexclude]
    return outnames




# average_mm_df - 9 lines
def average_mm_df( jmm_in, diagnostic_n=25, corr_thresh=0.9, verbose=False ):
    """
    jmrowavg, jmmcolavg, diagnostics = antspymm.average_mm_df( jmm_in, verbose=True )
    """

    jmm = jmm_in.copy()
    dxcols=['subjectid1','subjectid2','modalityid','joinid','correlation','distance']
    joinDiagnostics = pd.DataFrame( columns = dxcols )
    nanList=[math.nan]


# remove_unwanted_columns - 9 lines
def remove_unwanted_columns(df):
    # Identify columns to drop: those named 'X' or starting with 'Unnamed'
    cols_to_drop = [col for col in df.columns if col == 'X' or col.startswith('Unnamed')]
    
    # Drop the identified columns from the DataFrame, if any
    df_cleaned = df.drop(columns=cols_to_drop, errors='ignore')
    
    return df_cleaned



# average_blind_qc_by_modality - 36 lines
def average_blind_qc_by_modality(qc_full,verbose=False):
    """
    Averages time series qc results to yield one entry per image. this also filters to "known" columns.

    Args:
    qc_full: pandas dataframe containing the full qc data.

    Returns:
    pandas dataframe containing the processed qc data.
    """
    qc_full = remove_unwanted_columns( qc_full )
    # Get unique modalities
    modalities = qc_full['modality'].unique()
    modalities = modalities[modalities != 'unknown']
    # Get unique ids
    uid = qc_full['filename']
    to_average = uid.unique()
    meta = pd.DataFrame(columns=qc_full.columns )
    # Process each unique id
    n = len(to_average)
    for k in range(n):
        if verbose:
            if k % 100 == 0:
                progger = str( np.round( k / n * 100 ) )
                print( progger, end ="...", flush=True)
        m1sel = uid == to_average[k]
        if sum(m1sel) > 1:
            # If more than one entry for id, take the average of continuous columns,
            # maximum of the slice column, and the first entry of the other columns
            mfsub = process_dataframe_generalized(qc_full[m1sel],'filename')
        else:
            mfsub = qc_full[m1sel]
        meta.loc[k] = mfsub.iloc[0]
    meta['modality'] = meta['modality'].replace(['DTIdwi', 'DTIb0'], 'DTI', regex=True)
    return meta



# replace_elements_in_numpy_array - 40 lines
def replace_elements_in_numpy_array(original_array, indices_to_replace, new_value):
    """
    Replace specified elements or rows in a numpy array with a new value.

    Parameters:
    original_array (numpy.ndarray): A numpy array in which elements or rows are to be replaced.
    indices_to_replace (list or numpy.ndarray): Indices of elements or rows to be replaced.
    new_value: The new value to replace the specified elements or rows.

    Returns:
    numpy.ndarray: A new numpy array with the specified elements or rows replaced. If the input array is None,
                   the function returns None.
    """

    if original_array is None:
        return None

    max_index = original_array.size if original_array.ndim == 1 else original_array.shape[0]

    # Filter out invalid indices and check for any out-of-bounds indices
    valid_indices = []
    for idx in indices_to_replace:
        if idx < max_index:
            valid_indices.append(idx)
        else:
            warnings.warn(f"Warning: Index {idx} is out of bounds and will be ignored.")

    if original_array.ndim == 1:
        # Replace elements in a 1D array
        original_array[valid_indices] = new_value
    elif original_array.ndim == 2:
        # Replace rows in a 2D array
        original_array[valid_indices, :] = new_value
    else:
        raise ValueError("original_array must be either 1D or 2D.")

    return original_array





# remove_elements_from_numpy_array - 25 lines
def remove_elements_from_numpy_array(original_array, indices_to_remove):
    """
    Remove specified elements or rows from a numpy array.

    Parameters:
    original_array (numpy.ndarray): A numpy array from which elements or rows are to be removed.
    indices_to_remove (list or numpy.ndarray): Indices of elements or rows to be removed.

    Returns:
    numpy.ndarray: A new numpy array with the specified elements or rows removed. If the input array is None,
                   the function returns None.
    """

    if original_array is None:
        return None

    if original_array.ndim == 1:
        # Remove elements from a 1D array
        return np.delete(original_array, indices_to_remove)
    elif original_array.ndim == 2:
        # Remove rows from a 2D array
        return np.delete(original_array, indices_to_remove, axis=0)
    else:
        raise ValueError("original_array must be either 1D or 2D.")



# remove_volumes_from_timeseries - 22 lines
def remove_volumes_from_timeseries(time_series, volumes_to_remove):
    """
    Remove specified volumes from a time series.

    :param time_series: ANTsImage representing the time series (4D image).
    :param volumes_to_remove: List of volume indices to remove.
    :return: ANTsImage with specified volumes removed.
    """
    if not isinstance(time_series, ants.core.ants_image.ANTsImage):
        raise ValueError("time_series must be an ANTsImage.")

    if time_series.dimension != 4:
        raise ValueError("time_series must be a 4D image.")

    # Create a boolean index for volumes to keep
    volumes_to_keep = [i for i in range(time_series.shape[3]) if i not in volumes_to_remove]

    # Select the volumes to keep
    filtered_time_series = ants.from_numpy( time_series.numpy()[..., volumes_to_keep] )

    return ants.copy_image_info( time_series, filtered_time_series )



# remove_elements_from_list - 14 lines
def remove_elements_from_list(original_list, elements_to_remove):
    """
    Remove specified elements from a list.

    Parameters:
    original_list (list): The original list from which elements will be removed.
    elements_to_remove (list): A list of elements that need to be removed from the original list.

    Returns:
    list: A new list with the specified elements removed.
    """
    return [element for element in original_list if element not in elements_to_remove]




# flatten_time_series - 10 lines
def flatten_time_series(time_series):
    """
    Flatten a 4D time series into a 2D array.
    
    :param time_series: A 4D numpy array where the last dimension is time.
    :return: A 2D numpy array where each row is a flattened volume.
    """
    n_volumes = time_series.shape[3]
    return time_series.reshape(-1, n_volumes).T



# loop_timeseries_censoring - 33 lines
def loop_timeseries_censoring(x, threshold=0.5, mask=None, n_features_sample=0.02, seed=42, verbose=True):
    """
    Censor high leverage volumes from a time series using Local Outlier Probabilities (LoOP).

    Parameters:
    x (ANTsImage): A 4D time series image.
    threshold (float): Threshold for determining high leverage volumes based on LoOP scores.
    mask (antsImage): restricts to a ROI
    n_features_sample (int/float): feature sample size default 0.01; if less than one then this is interpreted as a percentage of the total features otherwise it sets the number of features to be used
    seed (int): random seed
    verbose (bool)

    Returns:
    tuple: A tuple containing the censored time series (ANTsImage) and the indices of the high leverage volumes.
    """
    import warnings
    if x.shape[3] < 20: # just a guess at what we need here ...
        warnings.warn("Warning: the time dimension is < 20 - too few samples for loop. just return the original data.")
        return x, []
    if mask is None:
        flattened_series = flatten_time_series(x.numpy())
    else:
        flattened_series = ants.timeseries_to_matrix( x, mask )
    if verbose:
        print("loop_timeseries_censoring: flattened")
    loop_scores = calculate_loop_scores(flattened_series, n_features_sample=n_features_sample, seed=seed, verbose=verbose )
    high_leverage_volumes = np.where(loop_scores > threshold)[0]
    if verbose:
        print("loop_timeseries_censoring: High Leverage Volumes:", high_leverage_volumes)
    new_asl = remove_volumes_from_timeseries(x, high_leverage_volumes)
    return new_asl, high_leverage_volumes




# filter_df - 36 lines
def filter_df(indf, myprefix):
    """
    Process and filter a pandas DataFrame, removing certain columns, 
    filtering based on data types, computing the mean of numeric columns, 
    and adding a prefix to column names.

    Parameters:
    indf (pandas.DataFrame): The input DataFrame to be processed.
    myprefix (str): A string prefix to be added to the column names 
                    of the processed DataFrame.

    Steps:
    1. Removes columns with names containing 'Unnamed'.
    2. If the DataFrame has no rows, it returns the empty DataFrame.
    3. Filters out columns based on the type of the first element, 
       keeping those that are of type `object`, `int`, or `float`.
    4. Removes columns that are of `object` dtype.
    5. Calculates the mean of the remaining columns, skipping NaN values.
    6. Adds the specified `myprefix` to the column names.

    Returns:
    pandas.DataFrame: A transformed DataFrame with a single row containing 
                      the mean values of the filtered columns, and with 
                      column names prefixed as specified.
    """
    indf = indf.loc[:, ~indf.columns.str.contains('Unnamed*', na=False, regex=True)]
    if indf.shape[0] == 0:
        return indf
    nums = [isinstance(indf[col].iloc[0], (object, int, float)) for col in indf.columns]
    indf = indf.loc[:, nums]
    indf = indf.loc[:, indf.dtypes != 'object']
    indf = pd.DataFrame(indf.mean(axis=0, skipna=True)).T
    indf = indf.add_prefix(myprefix)
    return indf




# progress_reporter - 13 lines
    def progress_reporter(current_step, total_steps, width=50):
        # Calculate the proportion of progress
        progress = current_step / total_steps
        # Calculate the number of 'filled' characters in the progress bar
        filled_length = int(width * progress)
        # Create the progress bar string
        bar = '█' * filled_length + '-' * (width - filled_length)
        # Print the progress bar with percentage
        print(f'\rProgress: |{bar}| {int(100 * progress)}%', end='\r')
        # Print a new line when the progress is complete
        if current_step == total_steps:
            print()



# enantiomorphic_filling_without_mask - 37 lines
def enantiomorphic_filling_without_mask( image, axis=0, intensity='low' ):
    """
    Perform an enantiomorphic lesion filling on an image without a lesion mask.

    Args:
    image (antsImage): The ants image to flip and fill
    axis ( int ): the axis along which to reflect the image
    intensity ( str ) : low or high

    Returns:
    ants.ANTsImage: The image after enantiomorphic filling.
    """
    imagen = ants.iMath( image, 'Normalize' )
    imagen = ants.iMath( imagen, "TruncateIntensity", 1e-6, 0.98 )
    imagen = ants.iMath( imagen, 'Normalize' )
    # Create a mirror image (flipping left and right)
    mirror_image = ants.reflect_image(imagen, axis=0, tx='antsRegistrationSyNQuickRepro[s]' )['warpedmovout']

    # Create a symmetric version of the image by averaging the original and the mirror image
    symmetric_image = imagen * 0.5 + mirror_image * 0.5

    # Identify potential lesion areas by finding differences between the original and symmetric image
    difference_image = image - symmetric_image
    diffseg = ants.threshold_image(difference_image, "Otsu", 3 )
    if intensity == 'low':
        likely_lesion = ants.threshold_image( diffseg, 1,  1)
    else:
        likely_lesion = ants.threshold_image( diffseg, 3,  3)
    likely_lesion = ants.smooth_image( likely_lesion, 3.0 ).iMath("Normalize")
    lesionneg = ( imagen*0+1.0 ) - likely_lesion
    filled_image = ants.image_clone(imagen)    
    filled_image = imagen * lesionneg + mirror_image * likely_lesion

    return filled_image, diffseg





# renameit - 28 lines
def renameit(df, old_col_name, new_col_name):
    """
    Renames a column in a pandas DataFrame in place. Raises an error if the specified old column name does not exist.

    Parameters:
    - df: pandas.DataFrame
        The DataFrame in which the column is to be renamed.
    - old_col_name: str
        The current name of the column to be renamed.
    - new_col_name: str
        The new name for the column.
    
    Raises:
    - ValueError: If the old column name does not exist in the DataFrame.
    
    Returns:
    None
    """
    import warnings
    # Check if the old column name exists in the DataFrame
    if old_col_name not in df.columns:
        warnings.warn(f"The column '{old_col_name}' does not exist in the DataFrame.")
        return
    
    # Proceed with renaming the column if it exists
    df.rename(columns={old_col_name: new_col_name}, inplace=True)




# t1w_super_resolution_with_hemispheres - 96 lines
def t1w_super_resolution_with_hemispheres(
    t1img,
    model,
    dilation_amount=8,
    truncation=[0.001, 0.999],
    target_range=[0, 1],
    poly_order="hist",
    min_spacing=0.8,
    verbose=True
):
    """
    Perform hemisphere-aware super-resolution on a T1-weighted image using a segmentation-guided DBPN model.

    This function performs brain extraction, hemisphere labeling, and segmentation-aware
    super-resolution using the provided T1 image and model. If the resolution is sufficient,
    hemisphere labels guide targeted SR via the `siq.inference` function.

    Parameters
    ----------
    t1img : ANTsImage
        Input T1-weighted image.

    model : keras.Model
        Super-resolution model (e.g., from `siq.default_dbpn` or loaded from `.keras` file).

    dilation_amount : int
        Amount of dilation to apply around labeled regions before SR.

    truncation : list of float
        Percentile values used to truncate intensity before model inference.

    target_range : list of float
        Range to normalize input intensities for model input.

    poly_order : str or int
        Polynomial order or "hist" for histogram matching after SR.

    min_spacing : float 
        if the minimum input image spacing is less than this value, 
        the function will return the original image.  Default 0.8.

    verbose : bool
        If True, print progress updates.

    Returns
    -------
    ANTsImage
        Super-resolved T1-weighted image.
    """
    if np.min(ants.get_spacing(t1img)) < min_spacing:
        if verbose:
            print("Image resolution too high — skipping SR.")
        return t1img

    if verbose:
        print("Performing brain extraction...")
    brain_mask = antspyt1w.brain_extraction(t1img)
    brain = t1img * brain_mask

    if verbose:
        print("Begin template loading")
    tlrfn = antspyt1w.get_data('T_template0_LR', target_extension='.nii.gz')
    tfn = antspyt1w.get_data('T_template0', target_extension='.nii.gz')
    template = ants.image_read(tfn)
    template = (template * antspynet.brain_extraction(template, 't1')).iMath("Normalize")
    template_lr = ants.image_read(tlrfn)
    if verbose:
        print("Done template loading")

    if verbose:
        print("Labeling hemispheres...")
    hemi_seg = antspyt1w.label_hemispheres(brain, template, template_lr)

    # Combine segmentation and brain mask — label values 1, 2 (hemi) → 3, 4
    hemisphere_mask = hemi_seg + 2.0 * brain_mask

    if verbose:
        print("Starting segmentation-aware super-resolution...")
    sr_result = siq.inference(
        t1img,
        model,
        segmentation=hemisphere_mask,
        truncation=truncation,
        target_range=target_range,
        dilation_amount=dilation_amount,
        poly_order=poly_order,
        verbose=verbose
    )

    sr_image = sr_result['super_resolution'] if isinstance(sr_result, dict) else sr_result

    if verbose:
        print("Done super-resolution.")
    return sr_image



