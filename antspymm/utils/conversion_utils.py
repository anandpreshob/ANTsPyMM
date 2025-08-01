"""
Data conversion utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import pandas as pd
import numpy as np

# Import nibabel and ants conditionally
try:
    import nibabel as nib
except ImportError:
    nib = None

try:
    import ants
except ImportError:
    ants = None

# Import ants_to_nibabel_affine from transform_utils
from .transform_utils import ants_to_nibabel_affine


def filter_columns_by_nan_percentage(df, max_nan_percentage=50.0):
    """
    Filter columns in a DataFrame based on a threshold for the percentage of NaN values.
    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame from which columns are to be filtered.
    max_nan_percentage : float, optional
        The maximum allowed percentage of NaN values in a column. Columns with a higher
        percentage of NaN values than this threshold will be removed from the DataFrame.
        The default is 50.0, which means columns with more than 50% NaN values will be removed.
    Returns
    -------
    pandas.DataFrame
        A DataFrame with columns filtered based on the NaN values percentage criterion.
    """
    if df.empty:
        return df
    
    # Calculate the percentage of NaN values for each column
    nan_percentage = (df.isnull().sum() / len(df)) * 100
    
    # Filter columns where NaN percentage is <= max_nan_percentage
    columns_to_keep = nan_percentage[nan_percentage <= max_nan_percentage].index
    
    # Return the filtered DataFrame
    return df[columns_to_keep]


def get_valid_modalities( long=False, asString=False, qc=False ):
    """
    return a list of valid modality identifiers used in NRG modality designation
    and that can be processed by this package.

    long - return the long version

    asString - concat list to string
    """
    if long:
        mymod = ["T1w", "NM2DMT", "rsfMRI", "rsfMRI_LR", "rsfMRI_RL", "rsfMRILR", "rsfMRIRL", "DTI", "DTI_LR","DTI_RL",  "DTILR","DTIRL","T2Flair", "dwi", "dwi_ap", "dwi_pa", "func", "func_ap", "func_pa", "perf", 'pet3d']
    elif qc:
        mymod = [ 'T1w', 'T2Flair', 'NM2DMT', 'DTI', 'DTIdwi','DTIb0', 'rsfMRI', "perf", 'pet3d' ]
    else:
        mymod = ["T1w", "NM2DMT", "DTI","T2Flair", "rsfMRI", "perf", 'pet3d' ]
    if not asString:
        return mymod
    else:
        mymodchar=""
        for x in mymod:
            mymodchar = mymodchar + " " + str(x)
        return mymodchar


def nrg_2_bids( nrg_filename ):
    """
    Convert an NRG filename to BIDS path/filename.

    Parameters:
    nrg_filename (str): The NRG filename to convert.

    Returns:
    str: The BIDS path/filename.
    """

    # Split the NRG filename into its components
    nrg_dirname, nrg_basename = os.path.split(nrg_filename)
    nrg_suffix = '.' + nrg_basename.split('.',1)[-1]
    nrg_basename = nrg_basename.replace(nrg_suffix, '') # remove ext
    nrg_parts = nrg_basename.split('-')
    nrg_subject_id = nrg_parts[1]
    nrg_modality = nrg_parts[3]
    nrg_repeat= nrg_parts[4]

    # Build the BIDS path/filename
    bids_dirname = os.path.join(nrg_dirname, 'bids')
    bids_subject = f'sub-{nrg_subject_id}'
    bids_session = f'ses-{nrg_repeat}'

    valid_modalities = get_valid_modalities()
    if nrg_modality is not None:
        if not nrg_modality in valid_modalities:
            raise ValueError('nrg_modality ' + str(nrg_modality) + " not a valid mm modality:  " + get_valid_modalities(asString=True))

    if nrg_modality == 'T1w' :
        bids_modality_folder = 'anat'
        bids_modality_filename = 'T1w'

    if nrg_modality == 'T2Flair' :
        bids_modality_folder = 'anat'
        bids_modality_filename = 'flair'

    if nrg_modality == 'NM2DMT' :
        bids_modality_folder = 'anat'
        bids_modality_filename = 'nm2dmt'

    if nrg_modality == 'DTI' or nrg_modality == 'DTI_RL' or nrg_modality == 'DTI_LR' :
        bids_modality_folder = 'dwi'
        bids_modality_filename = 'dwi'

    if nrg_modality == 'rsfMRI' or nrg_modality == 'rsfMRI_RL' or nrg_modality == 'rsfMRI_LR' :
        bids_modality_folder = 'func'
        bids_modality_filename = 'func'

    if nrg_modality == 'perf'  :
        bids_modality_folder = 'perf'
        bids_modality_filename = 'perf'

    bids_suffix = nrg_suffix[1:]
    bids_filename = f'{bids_subject}_{bids_session}_{bids_modality_filename}.{bids_suffix}'

    # Return bids filepath/filename
    return os.path.join(bids_dirname, bids_subject, bids_session, bids_modality_folder, bids_filename)


def bids_2_nrg( bids_filename, project_name, date, nrg_modality=None ):
    """
    Convert a BIDS filename to NRG path/filename.

    Parameters:
    bids_filename (str): The BIDS filename to convert
    project_name (str) : Name of project (i.e. PPMI)
    date (str) : Date of image acquisition


    Returns:
    str: The NRG path/filename.
    """

    bids_dirname, bids_basename = os.path.split(bids_filename)
    bids_suffix = '.'+ bids_basename.split('.',1)[-1]
    bids_basename = bids_basename.replace(bids_suffix, '') # remove ext
    bids_parts = bids_basename.split('_')
    nrg_subject_id = bids_parts[0].replace('sub-','')
    nrg_image_id = bids_parts[1].replace('ses-', '')
    bids_modality = bids_parts[2]
    valid_modalities = get_valid_modalities()
    if nrg_modality is not None:
        if not nrg_modality in valid_modalities:
            raise ValueError('nrg_modality ' + str(nrg_modality) + " not a valid mm modality: " + get_valid_modalities(asString=True))

    if bids_modality == 'T1w' and nrg_modality is None :
        nrg_modality = 'T1w'

    if bids_modality == 'flair' and nrg_modality is None :
        nrg_modality = 'T2Flair'

    if bids_modality == 'dwi' and nrg_modality is None  :
        nrg_modality = 'DTI'

    if bids_modality == 'func' and nrg_modality is None  :
        nrg_modality = 'rsfMRI'

    if bids_modality == 'perf' and nrg_modality is None  :
        nrg_modality = 'perf'

    nrg_suffix = bids_suffix[1:]
    nrg_filename = f'{project_name}-{nrg_subject_id}-{date}-{nrg_modality}-{nrg_image_id}.{nrg_suffix}'

    return os.path.join(project_name, nrg_subject_id, date, nrg_modality, nrg_image_id,nrg_filename)


def dict_to_dataframe(data_dict, convert_lists=True, convert_arrays=True, convert_images=True, verbose=False):
    """
    Convert a dictionary to a pandas DataFrame, excluding items that cannot be processed by pandas.

    :param data_dict: Dictionary to be converted.
    :param convert_lists: boolean
    :param convert_arrays: boolean
    :param convert_images: boolean
    :param verbose: boolean
    :return: DataFrame representation of the dictionary.
    """
    processed_data = {}
    list_length = None
    def mean_of_list(lst):
        if not lst:  # Check if the list is not empty
            return 0  # Return 0 or appropriate value for an empty list
        all_numeric = all(isinstance(item, (int, float)) for item in lst)
        if all_numeric:
            return sum(lst) / len(lst)
        return None
    
    for key, value in data_dict.items():
        # Check if value is a scalar
        if isinstance(value, (int, float, str, bool)):
            processed_data[key] = [value]
        # Check if value is a list of scalars
        elif isinstance(value, list) and all(isinstance(item, (int, float, str, bool)) for item in value) and convert_lists:
            meanvalue = mean_of_list( value )
            newkey = key+"_mean"
            if verbose:
                print( " Key " + key + " is list with mean " + str(meanvalue) + " to " + newkey )
            if newkey not in data_dict.keys() and convert_lists and meanvalue is not None:
                processed_data[newkey] = meanvalue
        elif isinstance(value, np.ndarray) and convert_arrays:
            meanvalue = value.mean()
            newkey = key+"_mean"
            if verbose:
                print( " Key " + key + " is nparray with mean " + str(meanvalue) + " to " + newkey )
            if newkey not in data_dict.keys():
                processed_data[newkey] = meanvalue
        elif ants is not None and isinstance(value, ants.core.ants_image.ANTsImage ) and convert_images:
            meanvalue = value.mean()
            newkey = key+"_mean"
            if newkey not in data_dict.keys():
                if verbose:
                    print( " Key " + key + " is antsimage with mean " + str(meanvalue) + " to " + newkey )
                processed_data[newkey] = meanvalue
            else:
                if verbose:
                    print( " Key " + key + " is antsimage with mean " + str(meanvalue) + " but " + newkey + " already exists" )

    return pd.DataFrame.from_dict(processed_data)


def to_nibabel(img: "ants.core.ants_image.ANTsImage") -> "nib.Nifti1Image":
    """
    Convert an ANTsPy image to a Nibabel Nifti1Image in-memory, using correct spatial affine.

    Parameters:
        img (ants.ANTsImage): An image from ANTsPy.

    Returns:
        nib.Nifti1Image: The corresponding Nibabel image with spatial orientation in RAS.
    """
    if ants is None:
        raise ImportError("ants package is required for to_nibabel function")
    if nib is None:
        raise ImportError("nibabel package is required for to_nibabel function")
    
    array_data = img.numpy()  # get voxel data as NumPy array
    affine = ants_to_nibabel_affine(img)
    return nib.Nifti1Image(array_data, affine)