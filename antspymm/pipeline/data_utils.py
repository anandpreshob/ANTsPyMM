"""
Data and model utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import urllib.request
import zipfile

# Global data path
DATA_PATH = os.path.expanduser('~/.antspymm/')


def get_data( name=None, force_download=False, version=26, target_extension='.csv' ):
    """
    Get ANTsPyMM data filename

    The first time this is called, it will download data to ~/.antspymm.
    After, it will just read data from disk.  The ~/.antspymm may need to
    be periodically deleted in order to ensure data is current.

    Arguments
    ---------
    name : string
        name of data tag to retrieve
        Options:
            - 'all'

    force_download: boolean

    version: version of data to download (integer)

    Returns
    -------
    string
        filepath of selected data

    Example
    -------
    >>> import antspymm
    >>> antspymm.get_data()
    """
    os.makedirs(DATA_PATH, exist_ok=True)

    def download_data(version):
        url = f"https://figshare.com/ndownloader/articles/22488978/versions/{version}"
        target_file = os.path.join(DATA_PATH, f'antspymm_data_v{version}.zip')
        if not os.path.exists(target_file) or force_download:
            urllib.request.urlretrieve(url, target_file)
            # unzip the file 
            with zipfile.ZipFile(target_file, 'r') as zip_ref:
                zip_ref.extractall(DATA_PATH)

    # check if we have any data locally
    datafileglob = os.path.join(DATA_PATH,"*"+target_extension)
    import glob
    myfiles = glob.glob(datafileglob)
    # if no data, get it
    if len(myfiles) == 0 or force_download:
        download_data(version)
        myfiles = glob.glob(datafileglob)

    if name is None:
        return myfiles[0]
    
    if name == 'all':
        return myfiles
    
    # search for the name in files
    for fn in myfiles:
        if name in fn:
            return fn
    
    # if not found, return first file
    if len(myfiles) > 0:
        return myfiles[0]
    else:
        raise FileNotFoundError(f"No data files found with pattern {datafileglob}")


def get_models( version=3, force_download=True ):
    """
    Get ANTsPyMM model filename

    The first time this is called, it will download models to ~/.antspymm.
    After, it will just read models from disk.  The ~/.antspymm may need to
    be periodically deleted in order to ensure models are current.

    Arguments
    ---------
    version: version of models to download (integer)

    force_download: boolean

    Returns
    -------
    string
        filepath of model directory

    Example
    -------
    >>> import antspymm
    >>> antspymm.get_models()
    """
    os.makedirs(DATA_PATH, exist_ok=True)

    def download_models(version):
        url = f"https://figshare.com/ndownloader/articles/22113243/versions/{version}"
        target_file = os.path.join(DATA_PATH, f'antspymm_models_v{version}.zip')
        if not os.path.exists(target_file) or force_download:
            urllib.request.urlretrieve(url, target_file)
            # unzip the file 
            with zipfile.ZipFile(target_file, 'r') as zip_ref:
                zip_ref.extractall(DATA_PATH)

    models_dir = os.path.join(DATA_PATH, 'models')
    
    # check if we have models locally
    if not os.path.exists(models_dir) or force_download:
        download_models(version)
    
    if os.path.exists(models_dir):
        return models_dir
    else:
        raise FileNotFoundError(f"Models directory not found at {models_dir}")