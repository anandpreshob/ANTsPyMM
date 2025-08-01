"""
Qc_Advanced functions for ANTsPyMM
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

# mm_match_by_qc_scoring
def mm_match_by_qc_scoring(df_a, df_b, match_column, criteria, prefix='matched_', exclude_columns=None):
    """
    Match each row in df_a to a row in df_b based on a matching column and criteria for selecting the best match,
    with options to prefix column names from df_b and exclude certain columns from the final output. Additionally,
    returns a DataFrame containing rows from df_b that were not matched to any row in df_a.

    Parameters:
    - df_a: DataFrame A.
    - df_b: DataFrame B.
    - match_column: The column name on which rows should match between DataFrame A and B.
    - criteria: A dictionary where keys are column names and values are 'min' or 'max', indicating whether
                the column should be minimized or maximized for the best match.
    - prefix: A string prefix to add to column names from df_b in the final output to avoid duplication.
    - exclude_columns: A list of column names from df_b to exclude from the final output.
    
    Returns:
    - A tuple of two DataFrames: 
        1. A new DataFrame combining df_a with matched rows from df_b.
        2. A DataFrame containing rows from df_b that were not matched to df_a.
    """
    from scipy.stats import zscore
    df_a = df_a.loc[:, ~df_a.columns.str.startswith('Unnamed:')].copy()
    if df_b is not None:
        df_b = df_b.loc[:, ~df_b.columns.str.startswith('Unnamed:')].copy()
    else:
        return df_a, pd.DataFrame()
    
    # Normalize df_b based on criteria
    for col, crit in criteria.items():
        if crit == 'max':
            df_b.loc[df_b.index, f'score_{col}'] = zscore(-df_b[col])
        elif crit == 'min':
            df_b.loc[df_b.index, f'score_{col}'] = zscore(df_b[col])

    # Calculate 'best_score' by summing all score columns
    score_columns = [f'score_{col}' for col in criteria.keys()]
    df_b['best_score'] = df_b[score_columns].sum(axis=1)

    matched_indices = []  # Track indices of matched rows in df_b

    # Match rows
    matched_rows = []
    for _, row_a in df_a.iterrows():
        matches = df_b[df_b[match_column] == row_a[match_column]]
        if not matches.empty:
            best_idx = matches['best_score'].idxmin()
            best_match = matches.loc[best_idx]
            matched_indices.append(best_idx)  # Track this index as matched
            matched_rows.append(best_match)
        else:
            matched_rows.append(pd.Series(dtype='float64'))

    # Create a DataFrame from matched rows
    df_matched = pd.DataFrame(matched_rows).reset_index(drop=True)
    
    # Exclude specified columns and add prefix
    if exclude_columns is not None:
        df_matched = df_matched.drop(columns=exclude_columns, errors='ignore')
    df_matched = df_matched.rename(columns=lambda x: f"{prefix}{x}" if x != match_column and x in df_matched.columns else x)

    # Combine df_a with matched rows from df_b
    result_df = pd.concat([df_a.reset_index(drop=True), df_matched], axis=1)
    
    # Extract unmatched rows from df_b
    unmatched_df_b = df_b.drop(index=matched_indices).reset_index(drop=True)

    return result_df, unmatched_df_b




# mm_match_by_qc_scoring_all
def mm_match_by_qc_scoring_all( qc_dataframe, fix_LRRL=True, mysep='-', verbose=True ):
    """
    Processes a quality control (QC) DataFrame to perform modality-specific matching and filtering based
    on predefined criteria, optimizing for minimal outliers and noise, and maximal signal-to-noise ratio (SNR),
    expected value of randomness (EVR), and dimensionality time (dimt).

    This function iteratively matches dataframes derived from the QC dataframe for different imaging modalities,
    applying a series of filters to select the best matches based on the QC metrics. Matches are made with
    consideration to minimize outlier loop and noise, while maximizing SNR, EVR, and dimt for each modality.

    Parameters:
    ----------
    qc_dataframe : pandas.DataFrame
        The DataFrame containing QC metrics for different modalities and imaging data.
    fix_LRRL : bool, optional
    mysep : string, character such as - or _ the usual antspymm separator argument

    verbose : bool, optional
        If True, prints the progress and the shape of the DataFrame being processed in each step.

    Process:
    -------
    1. Standardizes modalities by merging DTI-related entries.
    2. Converts specific columns to appropriate data types for processing.
    3. Performs modality-specific matching and filtering based on the outlier column and criteria for each modality.
    4. Iteratively processes unmatched data for predefined modalities with specific prefixes to find further matches.
    
    Returns:
    -------
    pandas.DataFrame
        The matched and filtered DataFrame after applying all QC scoring and matching operations across specified modalities.

    """
    qc_dataframe=remove_unwanted_columns( qc_dataframe )
    qc_dataframe['modality'] = qc_dataframe['modality'].replace(['DTIdwi', 'DTIb0'], 'DTI', regex=True)
    qc_dataframe['filename']=qc_dataframe['filename'].astype(str)
    qc_dataframe['ol_loop']=qc_dataframe['ol_loop'].astype(float)
    qc_dataframe['ol_lof']=qc_dataframe['ol_lof'].astype(float)
    qc_dataframe['ol_lof_decision']=qc_dataframe['ol_lof_decision'].astype(float)
    outlier_column='ol_loop'
    mmdf0 = best_mmm( qc_dataframe, 'T1w', outlier_column=outlier_column, mysep=mysep )['filt']
    fldf = best_mmm( qc_dataframe, 'T2Flair', outlier_column=outlier_column, mysep=mysep  )['filt']
    nmdf = best_mmm( qc_dataframe, 'NM2DMT', outlier_column=outlier_column, mysep=mysep  )['filt']
    rsdf = best_mmm( qc_dataframe, 'rsfMRI', outlier_column=outlier_column, mysep=mysep  )['filt']
    dtdf = best_mmm( qc_dataframe, 'DTI', outlier_column=outlier_column, mysep=mysep  )['filt']
    pfdf = best_mmm( qc_dataframe, 'perf', outlier_column=outlier_column, mysep=mysep  )['filt']

    criteria = {'ol_loop': 'min', 'noise': 'min', 'snr': 'max', 'EVR': 'max', 'reflection_err':'min'}
    xcl = [ 'mrimfg', 'mrimodel','mriMagneticFieldStrength', 'dti_failed', 'rsf_failed', 'subjectID', 'date', 'subjectIDdate','repeat']
    # Assuming df_a and df_b are already loaded
    mmdf, undffl = mm_match_by_qc_scoring(mmdf0, fldf, 'subjectIDdate', criteria, 
                        prefix='T2Flair_', exclude_columns=xcl )

    mmdf, undfpf = mm_match_by_qc_scoring(mmdf, pfdf, 'subjectIDdate', criteria, 
                        prefix='perf_', exclude_columns=xcl )

    prefixes = ['NM1_', 'NM2_', 'NM3_', 'NM4_', 'NM5_', 'NM6_']  
    undfmod = nmdf  # Initialize 'undfmod' with 'nmdf' for the first iteration
    if undfmod is not None:
        if verbose:
            print('start NM')
            print( undfmod.shape )
        for prefix in prefixes:
            if undfmod.shape[0] > 50:
                mmdf, undfmod = mm_match_by_qc_scoring(mmdf, undfmod, 'subjectIDdate', criteria, prefix=prefix, exclude_columns=xcl)
                if verbose:
                    print( prefix )
                    print( undfmod.shape )

    criteria = {'ol_loop': 'min', 'noise': 'min', 'snr': 'max', 'EVR': 'max', 'dimt':'max'}
    # higher bvalues lead to more noise ...
    criteria = {'ol_loop': 'min', 'noise': 'min',  'dti_bvalueMax':'min',  'dimt':'max'}
    prefixes = ['DTI1_', 'DTI2_', 'DTI3_']  # List of prefixes for each matching iteration
    undfmod = dtdf
    if undfmod is not None:
        if verbose:
            print('start DT')
            print( undfmod.shape )
        for prefix in prefixes:
            if undfmod.shape[0] > 50:
                mmdf, undfmod = mm_match_by_qc_scoring(mmdf, undfmod, 'subjectIDdate', criteria, prefix=prefix, exclude_columns=xcl)
                if verbose:
                    print( prefix )
                    print( undfmod.shape )

    prefixes = ['rsf1_', 'rsf2_', 'rsf3_']  # List of prefixes for each matching iteration
    undfmod = rsdf  # Initialize 'undfmod' with 'nmdf' for the first iteration
    if undfmod is not None:
        if verbose:
            print('start rsf')
            print( undfmod.shape )
        for prefix in prefixes:
            if undfmod.shape[0] > 50:
                mmdf, undfmod = mm_match_by_qc_scoring(mmdf, undfmod, 'subjectIDdate', criteria, prefix=prefix, exclude_columns=xcl)
                if verbose:
                    print( prefix )
                    print( undfmod.shape )
    
    if fix_LRRL:
        #        mmdf=fix_LR_RL_stuff( mmdf, 'DTI1_filename', 'DTI2_filename', 'DTI1_dimt', 'DTI2_dimt')
        mmdf=fix_LR_RL_stuff( mmdf, 'rsf1_filename', 'rsf2_filename', 'rsf1_dimt', 'rsf2_dimt', 'rsf1_imageID', 'rsf2_imageID'  )
    else:
        import warnings
        warnings.warn("FIXME: should fix LR and RL situation for the DTI and rsfMRI")

    # now do the necessary replacements
    
    renameit( mmdf, 'perf_imageID', 'perfid' )
    renameit( mmdf, 'perf_filename', 'perffn' )
    renameit( mmdf, 'T2Flair_imageID', 'flairid' )
    renameit( mmdf, 'T2Flair_filename', 'flairfn' )
    renameit( mmdf, 'rsf1_imageID', 'rsfid1' )
    renameit( mmdf, 'rsf2_imageID', 'rsfid2' )
    renameit( mmdf, 'rsf1_filename', 'rsffn1' )
    renameit( mmdf, 'rsf2_filename', 'rsffn2' )
    renameit( mmdf, 'DTI1_imageID', 'dtid1' )
    renameit( mmdf, 'DTI2_imageID', 'dtid2' )
    renameit( mmdf, 'DTI3_imageID', 'dtid3' )
    renameit( mmdf, 'DTI1_filename', 'dtfn1' )
    renameit( mmdf, 'DTI2_filename', 'dtfn2' )
    renameit( mmdf, 'DTI3_filename', 'dtfn3' )
    for x in range(1,6):
        temp0="NM"+str(x)+"_imageID"
        temp1="nmid"+str(x)
        renameit( mmdf, temp0, temp1 )
        temp0="NM"+str(x)+"_filename"
        temp1="nmfn"+str(x)
        renameit( mmdf, temp0, temp1 )
    return mmdf




# fix_LR_RL_stuff
def fix_LR_RL_stuff(df, col1, col2, size_col1, size_col2, id1, id2 ):
    df_copy = df.copy()
    # Ensure columns contain strings for substring checks
    df_copy[col1] = df_copy[col1].astype(str)
    df_copy[col2] = df_copy[col2].astype(str)
    df_copy[id1] = df_copy[id1].astype(str)
    df_copy[id2] = df_copy[id2].astype(str)
    
    for index, row in df_copy.iterrows():
        col1_val = row[col1]
        col2_val = row[col2]
        size1 = row[size_col1]
        size2 = row[size_col2]
        
        # Check for 'RL' or 'LR' in each column and compare sizes
        if ('RL' in col1_val or 'LR' in col1_val) and ('RL' in col2_val or 'LR' in col2_val):
            continue
        elif 'RL' not in col1_val and 'LR' not in col1_val and 'RL' not in col2_val and 'LR' not in col2_val:
            if size1 < size2:
                df_copy.at[index, col1] = df_copy.at[index, col2]
                df_copy.at[index, size_col1] = df_copy.at[index, size_col2]
                df_copy.at[index, id1] = df_copy.at[index, id2]
                df_copy.at[index, size_col2] = 0
                df_copy.at[index, col2] = None
                df_copy.at[index, id2] = None
            else:
                df_copy.at[index, col2] = None
                df_copy.at[index, size_col2] = 0
                df_copy.at[index, id2] = None
        elif 'RL' in col1_val or 'LR' in col1_val:
            if size1 < size2:
                df_copy.at[index, col1] = df_copy.at[index, col2]
                df_copy.at[index, id1] = df_copy.at[index, id2]
                df_copy.at[index, size_col1] = df_copy.at[index, size_col2]
                df_copy.at[index, size_col2] = 0
                df_copy.at[index, col2] = None
                df_copy.at[index, id2] = None
            else:
                df_copy.at[index, col2] = None
                df_copy.at[index, id2] = None
                df_copy.at[index, size_col2] = 0
        elif 'RL' in col2_val or 'LR' in col2_val:
            if size2 < size1:
                df_copy.at[index, id2] = None
                df_copy.at[index, col2] = None
                df_copy.at[index, size_col2] = 0
            else:
                df_copy.at[index, col1] = df_copy.at[index, col2]
                df_copy.at[index, id1] = df_copy.at[index, id2]
                df_copy.at[index, size_col1] = df_copy.at[index, size_col2]
                df_copy.at[index, size_col2] = 0
                df_copy.at[index, col2] = None    
                df_copy.at[index, id2] = None    
    return df_copy




# check_pd_construction
    def check_pd_construction(data, columns):
        # Check if the length of columns matches the length of data in each row
        if all(len(row) == len(columns) for row in data):
            return True
        else:
            return False


# shorten_pymm_names
def shorten_pymm_names(x):
    """
    Shortens pmymm names by applying a series of regex substitutions.
    
    Parameters:
    x (str): The input string to be shortened
    
    Returns:
    str: The shortened string
    """
    xx = x.lower()
    xx = re.sub("_", ".", xx)  # Replace underscores with periods
    xx = re.sub("\.\.", ".", xx, flags=re.I)  # Replace double dots with single dot
    # Apply the following regex substitutions in order
    xx = re.sub("sagittal.stratum.include.inferior.longitidinal.fasciculus.and.inferior.fronto.occipital.fasciculus.","ilf.and.ifo", xx, flags=re.I)
    xx = re.sub(r"sagittal.stratum.include.inferior.longitidinal.fasciculus.and.inferior.fronto.occipital.fasciculus.", "ilf.and.ifo", xx, flags=re.I)
    xx = re.sub(r".cres.stria.terminalis.can.not.be.resolved.with.current.resolution.", "", 
xx, flags=re.I)
    xx = re.sub("_", ".", xx)  # Replace underscores with periods
    xx = re.sub(r"longitudinal.fasciculus", "l.fasc", xx, flags=re.I)
    xx = re.sub(r"corona.radiata", "cor.rad", xx, flags=re.I)
    xx = re.sub("central", "cent", xx, flags=re.I)
    xx = re.sub(r"deep.cit168", "dp.", xx, flags=re.I)
    xx = re.sub("cit168", "", xx, flags=re.I)
    xx = re.sub(".include", "", xx, flags=re.I)
    xx = re.sub("mtg.sn", "", xx, flags=re.I)
    xx = re.sub("brainstem", ".bst", xx, flags=re.I)
    xx = re.sub(r"rsfmri.", "rsf.", xx, flags=re.I)
    xx = re.sub(r"dti.mean.fa.", "dti.fa.", xx, flags=re.I)
    xx = re.sub("perf.cbf.mean.", "cbf.", xx, flags=re.I)
    xx = re.sub(".jhu.icbm.labels.1mm", "", xx, flags=re.I)
    xx = re.sub(".include.optic.radiation.", "", xx, flags=re.I)
    xx = re.sub("\.\.", ".", xx, flags=re.I)  # Replace double dots with single dot
    xx = re.sub("\.\.", ".", xx, flags=re.I)  # Replace double dots with single dot
    xx = re.sub("cerebellar.peduncle", "cereb.ped", xx, flags=re.I)
    xx = re.sub(r"anterior.limb.of.internal.capsule", "ant.int.cap", xx, flags=re.I)
    xx = re.sub(r"posterior.limb.of.internal.capsule", "post.int.cap", xx, flags=re.I)
    xx = re.sub("t1hier.", "t1.", xx, flags=re.I)
    xx = re.sub("anterior", "ant", xx, flags=re.I)
    xx = re.sub("posterior", "post", xx, flags=re.I)
    xx = re.sub("inferior", "inf", xx, flags=re.I)
    xx = re.sub("superior", "sup", xx, flags=re.I)
    xx = re.sub(r"dktcortex", ".ctx", xx, flags=re.I)
    xx = re.sub(".lravg", "", xx, flags=re.I)
    xx = re.sub("dti.mean.fa", "dti.fa", xx, flags=re.I)
    xx = re.sub(r"retrolenticular.part.of.internal", "rent.int.cap", xx, flags=re.I)
    xx = re.sub(r"iculus.could.be.a.part.of.ant.internal.capsule", "", xx, flags=re.I)  # Twice
    xx = re.sub(".fronto.occipital.", ".frnt.occ.", xx, flags=re.I)
    xx = re.sub(r".longitidinal.fasciculus.", ".long.fasc.", xx, flags=re.I)  # Twice
    xx = re.sub(".external.capsule", ".ext.cap", xx, flags=re.I)
    xx = re.sub("of.internal.capsule", ".int.cap", xx, flags=re.I)
    xx = re.sub("fornix.cres.stria.terminalis", "fornix.", xx, flags=re.I)
    xx = re.sub("capsule", "", xx, flags=re.I)
    xx = re.sub("and.inf.frnt.occ.fasciculus.", "", xx, flags=re.I)
    xx = re.sub("crossing.tract.a.part.of.mcp.", "", xx, flags=re.I)
    return xx[:40]  # Truncate to first 40 characters




# shorten_pymm_names2
def shorten_pymm_names2(x, verbose=False ):
    """
    Shortens pmymm names by applying a series of regex substitutions.

    Parameters:
    x (str): The input string to be shortened

    verbose (bool): explain the patterns and replacements and their impact

    Returns:
    str: The shortened string
    """
    # Define substitution patterns as tuples
    substitutions = [
        ("_", "."),  
        ("\.\.", "."),
        ("sagittal.stratum.include.inferior.longitidinal.fasciculus.and.inferior.fronto.occipital.fasciculus.","ilf.and.ifo"),
        (r"sagittal.stratum.include.inferior.longitidinal.fasciculus.and.inferior.fronto.occipital.fasciculus.", "ilf.and.ifo"),
        (r".cres.stria.terminalis.can.not.be.resolved.with.current.resolution.", ""),
        ("_", "."),
        (r"longitudinal.fasciculus", "l.fasc"),
        (r"corona.radiata", "cor.rad"),
        ("central", "cent"),
        (r"deep.cit168", "dp."),
        ("cit168", ""),
        (".include", ""),
        ("mtg.sn", ""),
        ("brainstem", ".bst"),
        (r"rsfmri.", "rsf."),
        (r"dti.mean.fa.", "dti.fa."),
        ("perf.cbf.mean.", "cbf."),
        (".jhu.icbm.labels.1mm", ""),
        (".include.optic.radiation.", ""),
        ("\.\.", "."),  # Replace double dots with single dot
        ("\.\.", "."),  # Replace double dots with single dot
        ("cerebellar.peduncle", "cereb.ped"),
        (r"anterior.limb.of.internal.capsule", "ant.int.cap"),
        (r"posterior.limb.of.internal.capsule", "post.int.cap"),
        ("t1hier.", "t1."),
        ("anterior", "ant"),
        ("posterior", "post"),
        ("inferior", "inf"),
        ("superior", "sup"),
        (r"dktcortex", ".ctx"),
        (".lravg", ""),
        ("dti.mean.fa", "dti.fa"),
        (r"retrolenticular.part.of.internal", "rent.int.cap"),
        (r"iculus.could.be.a.part.of.ant.internal.capsule", ""),  # Twice
        (".fronto.occipital.", ".frnt.occ."),
        (r".longitidinal.fasciculus.", ".long.fasc."),  # Twice
        (".external.capsule", ".ext.cap"),
        ("of.internal.capsule", ".int.cap"),
        ("fornix.cres.stria.terminalis", "fornix."),
        ("capsule", ""),
        ("and.inf.frnt.occ.fasciculus.", ""),
        ("crossing.tract.a.part.of.mcp.", "")
      ]

    # Apply substitutions in order
    for pattern, replacement in substitutions:
        if verbose:
            print("Pre " + x + " pattern "+pattern + " repl " + replacement )
        x = re.sub(pattern, replacement, x.lower(), flags=re.IGNORECASE)
        if verbose:
            print("Post " + x)

    return x[:40]  # Truncate to first 40 characters




