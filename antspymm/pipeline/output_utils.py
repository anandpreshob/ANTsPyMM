"""
Output and writing utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import pandas as pd

# Import conditionally
try:
    import ants
except ImportError:
    ants = None

# Import from our modules
from ..image_io_module.image_io import image_write_with_thumbnail
from ..image_io_module.dwi_io import write_bvals_bvecs
from ..utils.conversion_utils import dict_to_dataframe
from ..utils.data_utils import get_antsimage_keys


def write_mm( output_prefix, mm, mm_norm=None, t1wide=None, separator='_', verbose=False ):
    """
    write the tabular and normalization output of the mm function

    Parameters
    -------------

    output_prefix : prefix for file outputs - modality specific postfix will be added

    mm  : output of mm function for modality-space processing should be a dictionary with 
        dictionary entries for each modality.

    mm_norm : output of mm function for normalized processing

    t1wide : wide output data frame from t1 hierarchical

    separator : string or character separator for filenames

    verbose : boolean

    Returns
    ---------

    both csv and image files written to disk.  the primary outputs will be
    output_prefix + separator + 'mmwide.csv' and *norm.nii.gz images

    """
    from dipy.io.streamline import save_tractogram
    if mm_norm is not None:
        for mykey in mm_norm:
            tempfn = output_prefix + separator + mykey + '.nii.gz'
            if mm_norm[mykey] is not None:
                image_write_with_thumbnail( mm_norm[mykey], tempfn )
    thkderk = None
    if t1wide is not None:
        thkderk = t1wide.iloc[: , 1:]
    kkderk = None
    if 'kk' in mm:
        if mm['kk'] is not None:
            kkderk = mm['kk']['thickness_dataframe'].iloc[: , 1:]
            mykey='thickness_image'
            tempfn = output_prefix + separator + mykey + '.nii.gz'
            image_write_with_thumbnail( mm['kk'][mykey], tempfn )
    nmderk = None
    if 'NM' in mm:
        if mm['NM'] is not None:
            nmderk = mm['NM']['NM_dataframe_wide'].iloc[: , 1:]
            for mykey in get_antsimage_keys( mm['NM'] ):
                tempfn = output_prefix + separator + mykey + '.nii.gz'
                image_write_with_thumbnail( mm['NM'][mykey], tempfn, thumb=False )

    faderk = mdderk = fat1derk = mdt1derk = None

    if 'DTI' in mm:
        if mm['DTI'] is not None:
            mydti = mm['DTI']
            myop = output_prefix + separator
            ants.image_write( mydti['dti'],  myop + 'dti.nii.gz' )
            write_bvals_bvecs( mydti['bval_LR'], mydti['bvec_LR'], myop + 'reoriented' )
            image_write_with_thumbnail( mydti['dwi_LR_dewarped'],  myop + 'dwi.nii.gz' )
            image_write_with_thumbnail( mydti['dtrecon_LR_dewarp']['RGB'] ,  myop + 'DTIRGB.nii.gz' )
            image_write_with_thumbnail( mydti['jhu_labels'],  myop+'dtijhulabels.nii.gz', mydti['recon_fa'] )
            image_write_with_thumbnail( mydti['recon_fa'],  myop+'dtifa.nii.gz' )
            image_write_with_thumbnail( mydti['recon_md'],  myop+'dtimd.nii.gz' )
            image_write_with_thumbnail( mydti['b0avg'],  myop+'b0avg.nii.gz' )
            image_write_with_thumbnail( mydti['dwiavg'],  myop+'dwiavg.nii.gz' )
            faderk = mm['DTI']['recon_fa_summary'].iloc[: , 1:]
            mdderk = mm['DTI']['recon_md_summary'].iloc[: , 1:]
            fat1derk = mm['FA_summ'].iloc[: , 1:]
            mdt1derk = mm['MD_summ'].iloc[: , 1:]
    if 'tractography' in mm:
        if mm['tractography'] is not None:
            ofn = output_prefix + separator + 'tractogram.trk'
            if mm['tractography']['tractogram'] is not None:
                save_tractogram( mm['tractography']['tractogram'], ofn )
    cnxderk = None
    if 'tractography_connectivity' in mm:
        if mm['tractography_connectivity'] is not None:
            cnxderk = mm['tractography_connectivity']['connectivity_wide'].iloc[: , 1:] # NOTE: connectivity_wide is not much tested
            ofn = output_prefix + separator + 'dtistreamlineconn.csv'
            pd.DataFrame(mm['tractography_connectivity']['connectivity_matrix']).to_csv( ofn )

    dlist = [
        thkderk,
        kkderk,
        nmderk,
        faderk,
        mdderk,
        fat1derk,
        mdt1derk,
        cnxderk
        ]
    is_all_none = all(element is None for element in dlist)
    if is_all_none:
        mm_wide = pd.DataFrame({'u_hier_id': [output_prefix] })
    else:
        mm_wide = pd.concat( dlist, axis=1, ignore_index=False )

    mm_wide = mm_wide.copy()
    if 'NM' in mm:
        if mm['NM'] is not None:
            nmwide = dict_to_dataframe( mm['NM'] )
            if mm_wide.shape[0] > 0 and nmwide.shape[0] > 0:
                nmwide.set_index( mm_wide.index, inplace=True )
            mm_wide = pd.concat( [mm_wide, nmwide ], axis=1, ignore_index=False )
    if 'flair' in mm:
        if mm['flair'] is not None:
            myop = output_prefix + separator + 'wmh.nii.gz'
            pngfnb = output_prefix + separator + 'wmh_seg.png'
            ants.plot( mm['flair']['flair'], mm['flair']['WMH_posterior_probability_map'], axis=2, nslices=21, ncol=7, filename=pngfnb, crop=True )
            if mm['flair']['WMH_probability_map'] is not None:
                image_write_with_thumbnail( mm['flair']['WMH_probability_map'], myop, thumb=False )
            flwide = dict_to_dataframe( mm['flair'] )
            if mm_wide.shape[0] > 0 and flwide.shape[0] > 0:
                flwide.set_index( mm_wide.index, inplace=True )
            mm_wide = pd.concat( [mm_wide, flwide ], axis=1, ignore_index=False )
    if 'rsf' in mm:
        if mm['rsf'] is not None:
            fcnxpro=99
            rsfdata = mm['rsf']
            if not isinstance( rsfdata, list ):
                rsfdata = [ rsfdata ]
            for rsfpro in rsfdata:
                fcnxpro=str( rsfpro['paramset']  )
                pronum = 'fcnxpro'+str(fcnxpro)+"_"
                if verbose:
                    print("Collect rsf data " + pronum)
                new_rsf_wide = dict_to_dataframe( rsfpro )
                new_rsf_wide = pd.concat( [new_rsf_wide, rsfpro['corr_wide'] ], axis=1, ignore_index=False )
                new_rsf_wide = new_rsf_wide.add_prefix( pronum )
                new_rsf_wide.set_index( mm_wide.index, inplace=True )
                ofn = output_prefix + separator + pronum + '.csv'
                new_rsf_wide.to_csv( ofn )
                mm_wide = pd.concat( [mm_wide, new_rsf_wide ], axis=1, ignore_index=False )
                for mykey in get_antsimage_keys( rsfpro ):
                    myop = output_prefix + separator + pronum + mykey + '.nii.gz'
                    image_write_with_thumbnail( rsfpro[mykey], myop, thumb=True )
                ofn = output_prefix + separator + pronum + 'rsfcorr.csv'
                rsfpro['corr'].to_csv( ofn )
                # apply same principle to new correlation matrix, doesn't need to be incorporated with mm_wide
                ofn2 = output_prefix + separator + pronum + 'nodescorr.csv'
                rsfpro['fullCorrMat'].to_csv( ofn2 )
    if 'DTI' in mm:
        if mm['DTI'] is not None:
            mydti = mm['DTI']
            mm_wide['dti_tsnr_b0_mean'] =  mydti['tsnr_b0'].mean()
            mm_wide['dti_tsnr_dwi_mean'] =  mydti['tsnr_dwi'].mean()
            mm_wide['dti_dvars_b0_mean'] =  mydti['dvars_b0'].mean()
            mm_wide['dti_dvars_dwi_mean'] =  mydti['dvars_dwi'].mean()
            mm_wide['dti_ssnr_b0_mean'] =  mydti['ssnr_b0'].mean()
            mm_wide['dti_ssnr_dwi_mean'] =  mydti['ssnr_dwi'].mean()
            mm_wide['dti_fa_evr'] =  mydti['fa_evr']
            mm_wide['dti_fa_SNR'] =  mydti['fa_SNR']
            if mydti['framewise_displacement'] is not None:
                mm_wide['dti_high_motion_count'] =  mydti['high_motion_count']
                mm_wide['dti_FD_mean'] = mydti['framewise_displacement'].mean()
                mm_wide['dti_FD_max'] = mydti['framewise_displacement'].max()
                mm_wide['dti_FD_sd'] = mydti['framewise_displacement'].std()
                fdfn = output_prefix + separator + '_fd.csv'
            else:
                mm_wide['dti_FD_mean'] = mm_wide['dti_FD_max'] = mm_wide['dti_FD_sd'] = 'NA'

    if 'perf' in mm:
        if mm['perf'] is not None:
            perfpro = mm['perf']
            prwide = dict_to_dataframe( perfpro )
            if mm_wide.shape[0] > 0 and prwide.shape[0] > 0:
                prwide.set_index( mm_wide.index, inplace=True )
            mm_wide = pd.concat( [mm_wide, prwide ], axis=1, ignore_index=False )
            if 'perf_dataframe' in perfpro.keys():
                pderk = perfpro['perf_dataframe'].iloc[: , 1:]
                pderk.set_index( mm_wide.index, inplace=True )
                mm_wide = pd.concat( [ mm_wide, pderk ], axis=1, ignore_index=False )
            else:
                print("FIXME - perfusion dataframe")
            for mykey in get_antsimage_keys( mm['perf'] ):
                tempfn = output_prefix + separator + mykey + '.nii.gz'
                image_write_with_thumbnail( mm['perf'][mykey], tempfn, thumb=False )

    if 'pet3d' in mm:
        if mm['pet3d'] is not None:
            pet3dpro = mm['pet3d']
            prwide = dict_to_dataframe( pet3dpro )
            if mm_wide.shape[0] > 0 and prwide.shape[0] > 0:
                prwide.set_index( mm_wide.index, inplace=True )
            mm_wide = pd.concat( [mm_wide, prwide ], axis=1, ignore_index=False )
            if 'pet3d_dataframe' in pet3dpro.keys():
                pderk = pet3dpro['pet3d_dataframe'].iloc[: , 1:]
                pderk.set_index( mm_wide.index, inplace=True )
                mm_wide = pd.concat( [ mm_wide, pderk ], axis=1, ignore_index=False )
            else:
                print("FIXME - pet3dusion dataframe")
            for mykey in get_antsimage_keys( mm['pet3d'] ):
                tempfn = output_prefix + separator + mykey + '.nii.gz'
                image_write_with_thumbnail( mm['pet3d'][mykey], tempfn, thumb=False )

    mmwidefn = output_prefix + separator + 'mmwide.csv'
    mm_wide.to_csv( mmwidefn )
    if verbose:
        print( output_prefix + " write_mm done." )