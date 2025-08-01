"""
Data Processing functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# generate_mm_dataframe - 171 lines
def generate_mm_dataframe(
        projectID,
        subjectID,
        date,
        imageUniqueID,
        modality,
        source_image_directory,
        output_image_directory,
        t1_filename,
        flair_filename=[],
        rsf_filenames=[],
        dti_filenames=[],
        nm_filenames=[],
        perf_filename=[],
        pet3d_filename=[],
):
    """
    Generate a DataFrame for medical imaging data with extensive validation of input parameters.

    This function creates a DataFrame containing information about medical imaging files,
    ensuring that filenames match expected patterns for their modalities and that all
    required images exist. It also validates the number of filenames provided for specific
    modalities like rsfMRI, DTI, and NM.

    Parameters:
    - projectID (str): Project identifier.
    - subjectID (str): Subject identifier.
    - date (str): Date of the imaging study.
    - imageUniqueID (str): Unique image identifier.
    - modality (str): Modality of the imaging study.
    - source_image_directory (str): Directory of the source images.
    - output_image_directory (str): Directory for output images.
    - t1_filename (str): Filename of the T1-weighted image.
    - flair_filename (list): List of filenames for FLAIR images.
    - rsf_filenames (list): List of filenames for rsfMRI images.
    - dti_filenames (list): List of filenames for DTI images.
    - nm_filenames (list): List of filenames for NM images.
    - perf_filename (list): List of filenames for perfusion images.
    - pet3d_filename (list): List of filenames for pet3d images.

    Returns:
    - pandas.DataFrame: A DataFrame containing the validated imaging study information.

    Raises:
    - ValueError: If any validation checks fail or if the number of columns does not match the data.
    """
    from os.path import exists
    valid_modalities = get_valid_modalities()
    if not isinstance(t1_filename, str):
        raise ValueError("t1_filename is not a string")
    if not exists(t1_filename):
        raise ValueError("t1_filename does not exist")
    if modality not in valid_modalities:
        raise ValueError('modality ' + str(modality) + " not a valid mm modality:  " + get_valid_modalities(asString=True))
    # if not exists( output_image_directory ):
    #    raise ValueError("output_image_directory does not exist")
    if not exists( source_image_directory ):
        raise ValueError("source_image_directory does not exist")
    if len( rsf_filenames ) > 2:
        raise ValueError("len( rsf_filenames ) > 2")
    if len( dti_filenames ) > 3:
        raise ValueError("len( dti_filenames ) > 3")
    if len( nm_filenames ) > 11:
        raise ValueError("len( nm_filenames ) > 11")
    if len( rsf_filenames ) < 2:
        for k in range(len(rsf_filenames),2):
            rsf_filenames.append(None)
    if len( dti_filenames ) < 3:
        for k in range(len(dti_filenames),3):
            dti_filenames.append(None)
    if len( nm_filenames ) < 10:
        for k in range(len(nm_filenames),10):
            nm_filenames.append(None)
    # check modality names
    if not "T1w" in t1_filename:
        raise ValueError("T1w is not in t1 filename " + t1_filename)
    if flair_filename is not None:
        if isinstance(flair_filename,list):
            if (len(flair_filename) == 0):
                flair_filename=None
            else:
                print("Take first entry from flair_filename list")
                flair_filename=flair_filename[0]
    if flair_filename is not None and not "lair" in flair_filename:
            raise ValueError("flair is not flair filename " + flair_filename)
    ## perfusion
    if perf_filename is not None:
        if isinstance(perf_filename,list):
            if (len(perf_filename) == 0):
                perf_filename=None
            else:
                print("Take first entry from perf_filename list")
                perf_filename=perf_filename[0]
    if perf_filename is not None and not "perf" in perf_filename:
            raise ValueError("perf_filename is not perf filename " + perf_filename)

    if pet3d_filename is not None:
        if isinstance(pet3d_filename,list):
            if (len(pet3d_filename) == 0):
                pet3d_filename=None
            else:
                print("Take first entry from pet3d_filename list")
                pet3d_filename=pet3d_filename[0]
    if pet3d_filename is not None and not "pet" in pet3d_filename:
            raise ValueError("pet3d_filename is not pet filename " + pet3d_filename)
    
    for k in nm_filenames:
        if k is not None:
            if not "NM" in k:
                raise ValueError("NM is not flair filename " + k)
    for k in dti_filenames:
        if k is not None:
            if not "DTI" in k and not "dwi" in k:
                raise ValueError("DTI/DWI is not dti filename " + k)
    for k in rsf_filenames:
        if k is not None:
            if not "fMRI" in k and not "func" in k:
                raise ValueError("rsfMRI/func is not rsfmri filename " + k)
    if perf_filename is not None:
        if not "perf" in perf_filename:
                raise ValueError("perf_filename is not a valid perfusion (perf) filename " + k)
    allfns = [t1_filename] + [flair_filename] + nm_filenames + dti_filenames + rsf_filenames + [perf_filename] + [pet3d_filename]
    for k in allfns:
        if k is not None:
            if not isinstance(k, str):
                raise ValueError(str(k) + " is not a string")
            if not exists( k ):
                raise ValueError( "image " + k + " does not exist")
    coredata = [
        projectID,
        subjectID,
        date,
        imageUniqueID,
        modality,
        source_image_directory,
        output_image_directory,
        t1_filename,
        flair_filename, 
        perf_filename,
        pet3d_filename]
    mydata0 = coredata +  rsf_filenames + dti_filenames
    mydata = mydata0 + nm_filenames
    corecols = [
        'projectID',
        'subjectID',
        'date',
        'imageID',
        'modality',
        'sourcedir',
        'outputdir',
        'filename',
        'flairid',
        'perfid',
        'pet3did']
    mycols0 = corecols + [
        'rsfid1', 'rsfid2',
        'dtid1', 'dtid2','dtid3']
    nmext = [
        'nmid1', 'nmid2', 'nmid3', 'nmid4', 'nmid5',
        'nmid6', 'nmid7','nmid8', 'nmid9', 'nmid10' #, 'nmid11'
    ]
    mycols = mycols0 + nmext
    if not check_pd_construction( [mydata], mycols ) :
#        print( mydata )
#        print( len(mydata ))
#        print( mycols )
#        print( len(mycols ))
        raise ValueError( "Error in generate_mm_dataframe: len( mycols ) != len( mydata ) which indicates a bad input parameter to this function." )
    studycsv = pd.DataFrame([ mydata ], columns=mycols)
    return studycsv



# generate_mm_dataframe_gpt - 79 lines
def generate_mm_dataframe_gpt(
        projectID, subjectID, date, imageUniqueID, modality, 
        source_image_directory, output_image_directory, t1_filename, 
        flair_filename=[], rsf_filenames=[], dti_filenames=[], nm_filenames=[], perf_filename=[] ):
    """
    see help for generate_mm_dataframe - same as this
    """
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





# nrg_filelist_to_dataframe - 35 lines
def nrg_filelist_to_dataframe( filename_list, myseparator="-" ):
    """
    convert a list of files in nrg format to a dataframe

    Arguments
    ---------
    filename_list : globbed list of files

    myseparator : string separator between nrg parts

    Returns
    -------

    df : pandas data frame

    """
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




# merge_timeseries_data - 25 lines
def merge_timeseries_data( img_LR, img_RL, allow_resample=True ):
    """
    merge time series data into space of reference_image

    img_LR : image

    img_RL : image

    allow_resample : boolean

    """
    # concatenate the images into the reference space
    mimg=[]
    for kk in range( img_LR.shape[3] ):
        temp = ants.slice_image( img_LR, axis=3, idx=kk )
        mimg.append( temp )
    for kk in range( img_RL.shape[3] ):
        temp = ants.slice_image( img_RL, axis=3, idx=kk )
        if kk == 0:
            insamespace = ants.image_physical_space_consistency( temp, mimg[0] )
        if allow_resample and not insamespace :
            temp = ants.resample_image_to_target( temp, mimg[0] )
        mimg.append( temp )
    return ants.list_to_ndimage( img_LR, mimg )



# merge_dwi_data - 34 lines
def merge_dwi_data( img_LRdwp, bval_LR, bvec_LR, img_RLdwp, bval_RL, bvec_RL ):
    """
    merge motion and distortion corrected data if possible

    img_LRdwp : image

    bval_LR : array

    bvec_LR : array

    img_RLdwp : image

    bval_RL : array

    bvec_RL : array

    """
    import warnings
    insamespace = ants.image_physical_space_consistency( img_LRdwp, img_RLdwp )
    if not insamespace :
        warnings.warn('not insamespace ... corrected image pair should occupy the same physical space; returning only the 1st set and wont join these data.')
        return img_LRdwp, bval_LR, bvec_LR
    
    bval_LR = np.concatenate([bval_LR,bval_RL])
    bvec_LR = np.concatenate([bvec_LR,bvec_RL])
    # concatenate the images
    mimg=[]
    for kk in range( img_LRdwp.shape[3] ):
            mimg.append( ants.slice_image( img_LRdwp, axis=3, idx=kk ) )
    for kk in range( img_RLdwp.shape[3] ):
            mimg.append( ants.slice_image( img_RLdwp, axis=3, idx=kk ) )
    img_LRdwp = ants.list_to_ndimage( img_LRdwp, mimg )
    return img_LRdwp, bval_LR, bvec_LR



# assemble_modality_specific_dataframes - 20 lines
def assemble_modality_specific_dataframes( mm_wide_csvs, hierdfin, nrg_modality, separator='-', progress=None, verbose=False ):
    moddersub = re.sub( "[*]","",nrg_modality)
    nmdf=pd.DataFrame()
    for k in range( hierdfin.shape[0] ):
        if progress is not None:
            if k % progress == 0:
                progger = str( np.round( k / hierdfin.shape[0] * 100 ) )
                print( progger, end ="...", flush=True)
        temp = mm_wide_csvs[k]
        mypartsf = temp.split("T1wHierarchical")
        myparts = mypartsf[0]
        t1iid = str(mypartsf[1].split("/")[1])
        fnsnm = glob.glob(myparts+"/" + nrg_modality + "/*/*" + t1iid + "*wide.csv")
        if len( fnsnm ) > 0 :
            for y in fnsnm:
                temp=read_mm_csv( y, colprefix=moddersub+'_', is_t1=False, separator=separator, verbose=verbose )
                if temp is not None:
                    nmdf=pd.concat( [nmdf, temp], axis=0, ignore_index=False )
    return nmdf



# merge_mm_dataframe - 7 lines
def merge_mm_dataframe(hierdf, mmdf, mm_suffix):
    try:
        hierdf = hierdf.merge(mmdf, on=['sid', 'visitdate', 't1imageuid'], suffixes=("",mm_suffix),how='left')
        return hierdf
    except KeyError:
        return hierdf



# process_dataframe_generalized - 15 lines
def process_dataframe_generalized(df, group_by_column):
    # Make sure the group_by_column is excluded from both numeric and other columns calculations
    numeric_cols = df.select_dtypes(include='number').columns.difference([group_by_column])
    other_cols = df.columns.difference(numeric_cols).difference([group_by_column])
    
    # Define aggregation functions: mean for numeric cols, mode for other cols
    # Update to handle empty mode results safely
    agg_dict = {col: 'mean' for col in numeric_cols}
    agg_dict.update({
        col: lambda x: pd.Series.mode(x).iloc[0] if not pd.Series.mode(x).empty else None for col in other_cols
    })    
    # Group by the specified column, applying different aggregation functions to different columns
    processed_df = df.groupby(group_by_column, as_index=False).agg(agg_dict)
    return processed_df



# aggregate_antspymm_results - 123 lines
def aggregate_antspymm_results(input_csv, subject_col='subjectID', date_col='date', image_col='imageID', date_column='ses-1', base_path="./Processed/ANTsExpArt/", hiervariable='T1wHierarchical', valid_modalities=None, verbose=False ):
    """
    Aggregate ANTsPyMM results from the specified CSV file and save the aggregated results to a new CSV file.

    Parameters:
    - input_csv (str): File path of the input CSV file containing ANTsPyMM QC results averaged and with outlier measurements.
    - subject_col (str): Name of the column to store subject IDs.
    - date_col (str): Name of the column to store date information.
    - image_col (str): Name of the column to store image IDs.
    - date_column (str): Name of the column representing the date information.
    - base_path (str): Base path for search paths. Defaults to "./Processed/ANTsExpArt/".
    - hiervariable (str) : the string variable denoting the Hierarchical output
    - valid_modalities (str array) : identifies for each modality; if None will be replaced by get_valid_modalities(long=True)
    - verbose : boolean

    Note:
    This function is tested under limited circumstances. Use with caution.

    Example usage:
    agg_df = aggregate_antspymm_results("qcdfaol.csv", subject_col='subjectID', date_col='date', image_col='imageID', date_column='ses-1', base_path="./Your/Custom/Path/")

    Author:
    Avants and ChatGPT
    """
    import pandas as pd
    import numpy as np
    from glob import glob

    import warnings
    # Warning message for untested function
    warnings.warn("Warning: This function is not well tested. Use with caution.")

    if valid_modalities is None:
        valid_modalities = get_valid_modalities('long')

    # Read the input CSV file
    df = pd.read_csv(input_csv)

    # Filter rows where modality is 'T1w'
    df = df[df['modality'] == 'T1w']
    badnames = get_names_from_data_frame( ['Unnamed'], df )
    df=df.drop(badnames, axis=1)

    # Add new columns for subject ID, date, and image ID
    df[subject_col] = np.nan
    df[date_col] = date_column
    df[image_col] = np.nan
    df = df.astype({subject_col: str, date_col: str, image_col: str })

#    if verbose:
#        print( df.shape )
#        print( df.dtypes )

    # prefilter df for data that exists
    keep = np.tile( False, df.shape[0] )
    for x in range(df.shape[0]):
        temp = df['filename'].iloc[x].split("_")
        # Generalized search paths
        path_template = f"{base_path}{temp[0]}/{date_column}/*/*/*"
        hierfn = sorted(glob( path_template + "-" + hiervariable + "-*wide.csv" ) )
        if len( hierfn ) > 0:
            keep[x]=True

    
    df=df[keep]
    
    if verbose:
        print( "original input had shape " + str( df.shape[0] ) + " (T1 only) and we find " + str( (keep).sum() ) + " with hierarchical output defined by variable: " + hiervariable )
        print( df.shape )

    myct = 0
    for x in range( df.shape[0]):
        if verbose:
            print(f"{x}...")
        locind = df.index[x]
        temp = df['filename'].iloc[x].split("_")
        if verbose:
            print( temp )
        df[subject_col].iloc[x]=temp[0]
        df[date_col].iloc[x]=date_column
        df[image_col].iloc[x]=temp[1]

        # Generalized search paths
        path_template = f"{base_path}{temp[0]}/{date_column}/*/*/*"
        if verbose:
            print(path_template)
        hierfn = sorted(glob( path_template + "-" + hiervariable + "-*wide.csv" ) )
        if len( hierfn ) > 0:
            hdf=t1df=dtdf=rsdf=perfdf=nmdf=flairdf=None
            if verbose:
                print(hierfn)
            hdf = pd.read_csv(hierfn[0])
            badnames = get_names_from_data_frame( ['Unnamed'], hdf )
            hdf=hdf.drop(badnames, axis=1)
            nums = [isinstance(hdf[col].iloc[0], (int, float)) for col in hdf.columns]
            corenames = list(np.array(hdf.columns)[nums])
            hdf.loc[:, nums] = hdf.loc[:, nums].add_prefix("T1Hier_")
            myct = myct + 1
            dflist = [hdf]

            for mymod in valid_modalities:
                t1wfn = sorted(glob( path_template+ "-" + mymod + "-*wide.csv" ) )
                if len( t1wfn ) > 0 :
                    if verbose:
                        print(t1wfn)
                    t1df = myread_csv(t1wfn[0], corenames)
                    t1df = filter_df( t1df, mymod+'_')
                    dflist = dflist + [t1df]
                
            hdf = pd.concat( dflist, axis=1, ignore_index=False )
            if verbose:
                print( df.loc[locind,'filename'] )
            if myct == 1:
                subdf = df.iloc[[x]]
                hdf.index = subdf.index.copy()
                df = pd.concat( [df,hdf], axis=1, ignore_index=False )
            else:
                commcols = list(set(hdf.columns).intersection(df.columns))
                df.loc[locind, commcols] = hdf.loc[0, commcols]
    badnames = get_names_from_data_frame( ['Unnamed'], df )
    df=df.drop(badnames, axis=1)
    return( df )



# aggregate_antspymm_results_sdf - 233 lines
def aggregate_antspymm_results_sdf(
    study_df, 
    project_col='projectID',
    subject_col='subjectID', 
    date_col='date', 
    image_col='imageID', 
    base_path="./", 
    hiervariable='T1wHierarchical', 
    splitsep='-',
    idsep='-',
    wild_card_modality_id=False,
    second_split=False,
    verbose=False ):
    """
    Aggregate ANTsPyMM results from the specified study data frame and store the aggregated results in a new data frame.  This assumes data is organized on disk 
    as follows:  rootdir/projectID/subjectID/date/outputid/imageid/ where 
    outputid is modality-specific and created by ANTsPyMM processing.

    Parameters:
    - study_df (pandas df): pandas data frame, output of generate_mm_dataframe.
    - project_col (str): Name of the column that stores the project ID
    - subject_col (str): Name of the column to store subject IDs.
    - date_col (str): Name of the column to store date information.
    - image_col (str): Name of the column to store image IDs.
    - base_path (str): Base path for searching for processing outputs of ANTsPyMM.
    - hiervariable (str) : the string variable denoting the Hierarchical output
    - splitsep (str):  the separator used to split the filename
    - idsep (str): the separator used to partition subjectid date and imageid 
        for example, if idsep is - then we have subjectid-date-imageid
    - wild_card_modality_id (bool): keep if False for safer execution
    - second_split (bool): this is a hack that will split the imageID by . and keep the first part of the split; may be needed when the input filenames contain .
    - verbose : boolean

    Note:
    This function is tested under limited circumstances. Use with caution.
    One particular gotcha is if the imageID is stored as a numeric value in the dataframe 
    but is meant to be a string.  E.g. '000' (string) would be interpreted as 0 in the 
    file name glob.  This would miss the extant (on disk) csv.

    Example usage:
    agg_df = aggregate_antspymm_results_sdf( studydf, subject_col='subjectID', date_col='date', image_col='imageID', base_path="./Your/Custom/Path/")

    Author:
    Avants and ChatGPT
    """
    import pandas as pd
    import numpy as np
    from glob import glob

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

    import warnings
    # Warning message for untested function
    warnings.warn("Warning: This function is not well tested. Use with caution.")

    vmoddict = {}
    # Add key-value pairs
    vmoddict['imageID'] = 'T1w'
    vmoddict['flairid'] = 'T2Flair'
    vmoddict['perfid'] = 'perf'
    vmoddict['pet3did'] = 'pet3d'
    vmoddict['rsfid1'] = 'rsfMRI'
#    vmoddict['rsfid2'] = 'rsfMRI'
    vmoddict['dtid1'] = 'DTI'
#    vmoddict['dtid2'] = 'DTI'
    vmoddict['nmid1'] = 'NM2DMT'
#    vmoddict['nmid2'] = 'NM2DMT'

    # Filter rows where modality is 'T1w'
    df = study_df[ study_df['modality'] == 'T1w']
    badnames = get_names_from_data_frame( ['Unnamed'], df )
    df=df.drop(badnames, axis=1)
    # prefilter df for data that exists
    keep = np.tile( False, df.shape[0] )
    for x in range(df.shape[0]):
        myfn = os.path.basename( df['filename'].iloc[x] )
        temp = myfn.split( splitsep )
        # Generalized search paths
        sid0 = str( temp[1] )
        sid = str( df[subject_col].iloc[x] )
        if sid0 != sid:
            warnings.warn("OUTER: the id derived from the filename " + sid0 + " does not match the id stored in the data frame " + sid )
            warnings.warn( "filename is : " +  myfn )
            warnings.warn( "sid is : " + sid )
            warnings.warn( "x is : " + str(x) )
        myproj = str(df[project_col].iloc[x])
        mydate = str(df[date_col].iloc[x])
        myid = str(df[image_col].iloc[x])
        if second_split:
            myid = myid.split(".")[0]
        path_template = base_path + "/" + myproj +  "/" + sid + "/" + mydate + '/' + hiervariable + '/' + str(myid) + "/"
        hierfn = sorted(glob( path_template + "*" + hiervariable + "*wide.csv" ) )
        if len( hierfn ) == 0:
            print( hierfn )
            print( path_template )
            print( myproj )
            print( sid )
            print( mydate ) 
            print( myid )
        if len( hierfn ) > 0:
            keep[x]=True

    # df=df[keep]
    if df.shape[0] == 0:
        warnings.warn("input data frame shape is filtered down to zero")
        return df

    if not df.index.is_unique:
        warnings.warn("data frame does not have unique indices.  we therefore reset the index to allow the function to continue on." )
        df = df.reset_index()

    
    if verbose:
        print( "original input had shape " + str( df.shape[0] ) + " (T1 only) and we find " + str( (keep).sum() ) + " with hierarchical output defined by variable: " + hiervariable )
        print( df.shape )

    dfout = pd.DataFrame()
    myct = 0
    for x in range( df.shape[0]):
        if verbose:
            print("\n\n-------------------------------------------------")
            print(f"{x}...")
        else:
            progress_reporter(x, df.shape[0], width=500)
        locind = df.index[x]
        myfn = os.path.basename( df['filename'].iloc[x] )
        sid = str( df[subject_col].iloc[x] )
        tempB = myfn.split( splitsep )
        sid0 = str(tempB[1])
        if sid0 != sid and verbose:
            warnings.warn("INNER: the id derived from the filename " + str(sid) + " does not match the id stored in the data frame " + str(sid0) )
            warnings.warn( "filename is : " +  str(myfn) )
            warnings.warn( "sid is : " + str(sid) )
            warnings.warn( "x is : " + str(x) )
            warnings.warn( "index is : " + str(locind) )
        myproj = str(df[project_col].iloc[x])
        mydate = str(df[date_col].iloc[x])
        myid = str(df[image_col].iloc[x])
        if second_split:
            myid = myid.split(".")[0]
        if verbose:
            print( myfn )
            print( temp )
            print( "id " + sid  )
        path_template = base_path + "/" + myproj +  "/" + sid + "/" + mydate + '/' + hiervariable + '/' + str(myid) + "/"
        searchhier = path_template + "*" + hiervariable + "*wide.csv"
        if verbose:
            print( searchhier )
        hierfn = sorted( glob( searchhier ) )
        if len( hierfn ) > 1:
            raise ValueError("there are " + str( len( hierfn ) ) + " number of hier fns with search path " + searchhier )
        if len( hierfn ) == 1:
            hdf=t1df=dtdf=rsdf=perfdf=nmdf=flairdf=None
            if verbose:
                print(hierfn)
            hdf = pd.read_csv(hierfn[0])
            if verbose:
                print( hdf['vol_hemisphere_lefthemispheres'] )
            badnames = get_names_from_data_frame( ['Unnamed'], hdf )
            hdf=hdf.drop(badnames, axis=1)
            nums = [isinstance(hdf[col].iloc[0], (int, float)) for col in hdf.columns]
            corenames = list(np.array(hdf.columns)[nums])
            # hdf.loc[:, nums] = hdf.loc[:, nums].add_prefix("T1Hier_")
            hdf = hdf.add_prefix("T1Hier_")
            myct = myct + 1
            dflist = [hdf]

            for mymod in vmoddict.keys():
                if verbose:
                    print("\n\n************************* " + mymod + " *************************")
                modalityclass = vmoddict[ mymod ]
                if wild_card_modality_id:
                    mymodid = '*'
                else:
                    mymodid = str( df[mymod].iloc[x] )
                    if mymodid.lower() != "nan" and mymodid.lower() != "na":
                        mymodid = os.path.basename( mymodid )
                        mymodid = os.path.splitext( mymodid )[0]
                        mymodid = os.path.splitext( mymodid )[0]
                        temp = mymodid.split( idsep )
                        mymodid = temp[ len( temp )-1 ]
                    else:
                        if verbose:
                            print("missing")
                        continue
                if verbose:
                    print( "modality id is " + mymodid + " for modality " + modalityclass + ' modality specific subj ' + sid + ' modality specific id is ' + myid + " its date " +  mydate )
                modalityclasssearch = modalityclass
                if modalityclass in ['rsfMRI','DTI']:
                    modalityclasssearch=modalityclass+"*"
                path_template_m = base_path + "/" + myproj +  "/" + sid + "/" + mydate + '/' + modalityclasssearch + '/' + mymodid + "/"
                modsearch = path_template_m + "*" + modalityclasssearch + "*wide.csv"
                if verbose:
                    print( modsearch )
                t1wfn = sorted( glob( modsearch ) )
                if len( t1wfn ) > 1:
                    nlarge = len(t1wfn)
                    t1wfn = find_most_recent_file( t1wfn )
                    warnings.warn("there are " + str( nlarge ) + " number of wide fns with search path " + modsearch + " we take the most recent of these " + t1wfn[0] )
                if len( t1wfn ) == 1:
                    if verbose:
                        print(t1wfn)
                    t1df = myread_csv(t1wfn[0], corenames)
                    t1df = filter_df( t1df, modalityclass+'_')
                    dflist = dflist + [t1df]
                else:
                    if verbose:
                        print( " cannot find " + modsearch )
                
            hdf = pd.concat( dflist, axis=1, ignore_index=False)
            if verbose:
                print( "count: " + str( myct ) )
            subdf = df.iloc[[x]]
            hdf.index = subdf.index.copy()
            subdf = pd.concat( [subdf,hdf], axis=1, ignore_index=False)
            dfout = pd.concat( [dfout,subdf], axis=0, ignore_index=False )

    if dfout.shape[0] > 0:
        badnames = get_names_from_data_frame( ['Unnamed'], dfout )
        dfout=dfout.drop(badnames, axis=1)
    return dfout


