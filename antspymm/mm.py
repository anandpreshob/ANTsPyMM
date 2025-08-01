
# Import from extracted modules
from .utils.string_utils import (
    nrg_filename_to_subjectvisit, parse_nrg_filename, validate_filename,
    validate_modality, nrg_format_path
)
from .utils.data_utils import get_antsimage_keys
from .utils.transform_utils import ants_to_nibabel_affine
from .utils.filesystem_utils import (
    validate_nrg_file_format, find_most_recent_file, clean_tmp_directory
)
from .utils.conversion_utils import (
    get_valid_modalities, nrg_2_bids, bids_2_nrg, dict_to_dataframe, to_nibabel,
    filter_columns_by_nan_percentage
)
from .image_io_module.image_io import mm_read, mm_read_to_3d, image_write_with_thumbnail
from .image_io_module.dwi_io import write_bvals_bvecs
from .processing.qc import (
    tsnr, dvars, mask_snr, slice_snr, foreground_background_snr, quantile_snr
)
from .processing.dti import bvec_reorientation, get_dti
from .processing.transforms import deformation_gradient_optimized
from .processing.segmentation import segment_timeseries_by_bvalue, segment_timeseries_by_meanvalue
from .pipeline.data_utils import get_data, get_models
from .pipeline.output_utils import write_mm

# Import from newly extracted modules
from .signal_processing.signal_processing import daniell_window_convolve, conv_circular
from .fmri.fmri import resting_state_fmri_networks, impute_timeseries, score_fmri_censoring
from .misc_utils.misc_utils import is_bst_region, docsamson, best_mmm, get_hemisphere_and_base, map_idps_to_rois
from .qc_advanced.qc_advanced import (
    mm_match_by_qc_scoring, mm_match_by_qc_scoring_all, fix_LR_RL_stuff, 
    check_pd_construction, shorten_pymm_names, shorten_pymm_names2
)
from .registration.registration import (
    dti_reg, timeseries_reg, mc_reg, transform_and_reorient_dti, apply_transforms_mixed_interpolation
)

# Import from final extraction modules
from .image_processing.image_processing import *
from .data_processing.data_processing import *
from .utility.utility import *
from .analysis.analysis import *
from .visualization.visualization import *
from .io_utils.io_utils import *
from .stats.stats import *
from .dwi.dwi import *

__all__ = ['version',
    'mm_read',
    'mm_read_to_3d',
    'image_write_with_thumbnail',
    'nrg_format_path',
    'highest_quality_repeat',
    'match_modalities',
    'mc_resample_image_to_target',
    'nrg_filelist_to_dataframe',
    'merge_timeseries_data',
    'timeseries_reg',
    'merge_dwi_data',
    'outlierness_by_modality',
    'bvec_reorientation',
    'get_dti',
    'dti_reg',
    'mc_reg',
    'get_data',
    'get_models',
    'get_valid_modalities',
    'dewarp_imageset',
    'super_res_mcimage',
    'segment_timeseries_by_meanvalue',
    'get_average_rsf',
    'get_average_dwi_b0',
    'dti_template',
    't1_based_dwi_brain_extraction',
    'mc_denoise',
    'tsnr',
    'dvars',
    'slice_snr',
    'impute_fa',
    'trim_dti_mask',
    'dipy_dti_recon',
    'concat_dewarp',
    'joint_dti_recon',
    'middle_slice_snr',
    'foreground_background_snr',
    'quantile_snr',
    'mask_snr',
    'dwi_deterministic_tracking',
    'dwi_closest_peak_tracking',
    'dwi_streamline_pairwise_connectivity',
    'dwi_streamline_connectivity',
    'hierarchical_modality_summary',
    'tra_initializer',
    'neuromelanin',
    'resting_state_fmri_networks',
    'write_bvals_bvecs',
    'crop_mcimage',
    'mm',
    'write_mm',
    'mm_nrg',
    'mm_csv',
    'collect_blind_qc_by_modality',
    'alffmap',
    'alff_image',
    'down2iso',
    'read_mm_csv',
    'assemble_modality_specific_dataframes',
    'bind_wide_mm_csvs',
    'merge_mm_dataframe',
    'augment_image',
    'boot_wmh',
    'threaded_bind_wide_mm_csvs',
    'get_names_from_data_frame',
    'average_mm_df',
    'quick_viz_mm_nrg',
    'blind_image_assessment',
    'average_blind_qc_by_modality',
    'best_mmm',
    'nrg_2_bids',
    'bids_2_nrg',
    'parse_nrg_filename',
    'novelty_detection_svm',
    'novelty_detection_ee',
    'novelty_detection_lof',
    'novelty_detection_loop',
    'novelty_detection_quantile',
    'generate_mm_dataframe',
    'aggregate_antspymm_results',
    'aggregate_antspymm_results_sdf',
    'study_dataframe_from_matched_dataframe',
    'merge_wides_to_study_dataframe',
    'filter_image_files',
    'docsamson',
    'enantiomorphic_filling_without_mask',
    'wmh',
    'remove_elements_from_numpy_array',
    'score_fmri_censoring',
    'remove_volumes_from_timeseries',
    'loop_timeseries_censoring',
    'clean_tmp_directory',
    'validate_nrg_file_format',
    'ants_to_nibabel_affine',
    'dict_to_dataframe']

from pathlib import Path
from pathlib import PurePath
import os
import pandas as pd
import math
import os.path
from os import path
import pickle
import sys
import numpy as np
import random
import functools
from operator import mul
from scipy.sparse.linalg import svds
from scipy.stats import pearsonr
import re
import datetime as dt
from collections import Counter
import tempfile
import uuid
import warnings

from dipy.core.histeq import histeq
import dipy.reconst.dti as dti
from dipy.core.gradients import (gradient_table, gradient_table_from_gradient_strength_bvecs)
from dipy.io.gradients import read_bvals_bvecs
from dipy.segment.mask import median_otsu
from dipy.reconst.dti import fractional_anisotropy, color_fa
import nibabel as nib

import ants
import antspynet
import antspyt1w
import siq
import tensorflow as tf

from multiprocessing import Pool
import glob as glob

antspyt1w.set_global_scientific_computing_random_seed(
    antspyt1w.get_global_scientific_computing_random_seed( )
)

DATA_PATH = os.path.expanduser('~/.antspymm/')

import pandas as pd
from os.path import exists

    from os.path import exists
    ex_path = os.path.expanduser( "~/.antspyt1w/" )
    ex_path_mm = os.path.expanduser( "~/.antspymm/" )
    mycsvfn = ex_path + "FA_JHU_labels_edited.csv"
    citcsvfn = ex_path + "CIT168_Reinf_Learn_v1_label_descriptions_pad.csv"
    dktcsvfn = ex_path + "dkt.csv"
    cnxcsvfn = ex_path + "dkt_cortex_cit_deep_brain.csv"
    JHU_atlasfn = ex_path + 'JHU-ICBM-FA-1mm.nii.gz' # Read in JHU atlas
    JHU_labelsfn = ex_path + 'JHU-ICBM-labels-1mm.nii.gz' # Read in JHU labels
    templatefn = ex_path + 'CIT168_T1w_700um_pad_adni.nii.gz'
    if not exists( mycsvfn ) or not exists( citcsvfn ) or not exists( cnxcsvfn ) or not exists( dktcsvfn ) or not exists( JHU_atlasfn ) or not exists( JHU_labelsfn ) or not exists( templatefn ):
        print( "**missing files** => call get_data from latest antspyt1w and antspymm." )
        raise ValueError('**missing files** => call get_data from latest antspyt1w and antspymm.')
    mycsv = pd.read_csv(  mycsvfn )
    citcsv = pd.read_csv(  os.path.expanduser( citcsvfn ) )
    dktcsv = pd.read_csv(  os.path.expanduser( dktcsvfn ) )
    cnxcsv = pd.read_csv(  os.path.expanduser( cnxcsvfn ) )
    JHU_atlas = mm_read( JHU_atlasfn ) # Read in JHU atlas
    JHU_labels = mm_read( JHU_labelsfn ) # Read in JHU labels
    template = mm_read( templatefn ) # Read in template
    if group_template is None:
        group_template = template
        group_transform = do_normalization['fwdtransforms']
    if verbose:
        print("Using group template:")
        print( group_template )
    #####################
    #  T1 hierarchical  #
    #####################
    t1imgbrn = hier['brain_n4_dnz']
    t1atropos = hier['dkt_parc']['tissue_segmentation']
    output_dict = {
        'kk': None,
        'rsf': None,
        'flair' : None,
        'NM' : None,
        'DTI' : None,
        'FA_summ' : None,
        'MD_summ' : None,
        'tractography' : None,
        'tractography_connectivity' : None,
        'perf' : None,
        'pet3d' : None,
    }
    normalization_dict = {
        'kk_norm': None,
        'NM_norm' : None,
        'DTI_norm': None,
        'FA_norm' : None,
        'MD_norm' : None,
        'perf_norm' : None,
        'alff_norm' : None,
        'falff_norm' : None,
        'CinguloopercularTaskControl_norm' : None,
        'DefaultMode_norm' : None,
        'MemoryRetrieval_norm' : None,
        'VentralAttention_norm' : None,
        'Visual_norm' : None,
        'FrontoparietalTaskControl_norm' : None,
        'Salience_norm' : None,
        'Subcortical_norm' : None,
        'DorsalAttention_norm' : None,
        'pet3d_norm' : None
    }
    if test_run:
        return output_dict, normalization_dict

    if do_kk:
        if verbose:
            print('kk in mm')
        output_dict['kk'] = antspyt1w.kelly_kapowski_thickness( t1_image,
            labels=hier['dkt_parc']['dkt_cortex'], iterations=45 )

    if perfusion_image is not None:
        if perfusion_image.shape[3] > 1: # FIXME - better heuristic?
            output_dict['perf'] = bold_perfusion(
                perfusion_image,
                t1_image,
                hier['brain_n4_dnz'],
                t1atropos,
                hier['dkt_parc']['dkt_cortex'] + hier['cit168lab'],
                n_to_trim = perfusion_trim,
                m0_image = perfusion_m0_image,
                m0_indices = perfusion_m0,
                verbose=verbose )

    if pet_3d_image is not None:
        if pet_3d_image.dimension == 3: # FIXME - better heuristic?
            output_dict['pet3d'] = pet3d_summary(
                pet_3d_image,
                t1_image,
                hier['brain_n4_dnz'],
                t1atropos,
                hier['dkt_parc']['dkt_cortex'] + hier['cit168lab'],
                verbose=verbose )
    ################################## do the rsf .....
    if len(rsf_image) > 0:
        my_motion_tx = 'antsRegistrationSyNRepro[r]'
        rsf_image = [i for i in rsf_image if i is not None]
        if verbose:
            print('rsf length ' + str( len( rsf_image ) ) )
        if len( rsf_image ) >= 2: # assume 2 is the largest possible value
            rsf_image1 = rsf_image[0]
            rsf_image2 = rsf_image[1]
            # build a template then join the images
            if verbose:
                print("initial average for rsf")
            rsfavg1, hlinds = loop_timeseries_censoring( rsf_image1, 0.1 )
            rsfavg1=get_average_rsf(rsfavg1)
            rsfavg2, hlinds = loop_timeseries_censoring( rsf_image2, 0.1 )
            rsfavg2=get_average_rsf(rsfavg2)
            if verbose:
                print("template average for rsf")
            init_temp = ants.image_clone( rsfavg1 )
            if rsf_image1.shape[3] < rsf_image2.shape[3]:
                init_temp = ants.image_clone( rsfavg2 )
            boldTemplate = ants.build_template(
                initial_template = init_temp,
                image_list=[rsfavg1,rsfavg2],
                type_of_transform="antsRegistrationSyNQuickRepro[s]",
                iterations=5, verbose=False )
            if verbose:
                print("join the 2 rsf")
            if rsf_image1.shape[3] > 10 and rsf_image2.shape[3] > 10:
                leadvols = list(range(8))
                rsf_image2 = remove_volumes_from_timeseries( rsf_image2, leadvols )
                rsf_image = merge_timeseries_data( rsf_image1, rsf_image2 )
            elif rsf_image1.shape[3] > rsf_image2.shape[3]:
                rsf_image = rsf_image1
            else:
                rsf_image = rsf_image2
        elif len( rsf_image ) == 1:
            rsf_image = rsf_image[0]
            boldTemplate, hlinds = loop_timeseries_censoring( rsf_image, 0.1 )
            boldTemplate = get_average_rsf(boldTemplate)
        if rsf_image.shape[3] > 10: # FIXME - better heuristic?
            rsfprolist = [] # FIXMERSF
            # Create the parameter DataFrame
            df = pd.DataFrame({
                "num": [134, 122, 129],
                "loop": [0.50, 0.25, 0.50],
                "cens": [True, True, True],
                "HM": [1.0, 5.0, 0.5],
                "ff": ["tight", "tight", "tight"],
                "CC": [5, 5, 0.8],
                "imp": [True, True, True],
                "up": [rsf_upsampling, rsf_upsampling, rsf_upsampling],
                "coords": [False,False,False]
            }, index=[0, 1, 2])
            for p in range(df.shape[0]):
                if verbose:
                    print("rsf parameters")
                    print( df.iloc[p] )
                if df['ff'].iloc[p] == 'broad':
                    f=[ 0.008, 0.15 ]
                elif df['ff'].iloc[p] == 'tight':
                    f=[ 0.03, 0.08 ]
                elif df['ff'].iloc[p] == 'mid':
                    f=[ 0.01, 0.1 ]
                elif df['ff'].iloc[p] == 'mid2':
                    f=[ 0.01, 0.08 ]
                else:
                    raise ValueError("we do not recognize this parameter choice for frequency filtering: " + df['ff'].iloc[p] )
                HM = df['HM'].iloc[p]
                CC = df['CC'].iloc[p]
                loop= df['loop'].iloc[p]
                cens =df['cens'].iloc[p]
                imp = df['imp'].iloc[p]
                rsf0 = resting_state_fmri_networks(
                                            rsf_image,
                                            boldTemplate,
                                            hier['brain_n4_dnz'],
                                            t1atropos,
                                            f=f,
                                            FD_threshold=HM, 
                                            spa = None, 
                                            spt = None, 
                                            nc = CC,
                                            outlier_threshold=loop,
                                            ica_components = 0,
                                            impute = imp,
                                            censor = cens,
                                            despike = 2.5,
                                            motion_as_nuisance = True,
                                            upsample=df['up'].iloc[p],
                                            clean_tmp=0.66,
                                            paramset=df['num'].iloc[p],
                                            powers=df['coords'].iloc[p],
                                            verbose=verbose ) # default
                rsfprolist.append( rsf0 )
            output_dict['rsf'] = rsfprolist

    if nm_image_list is not None:
        if verbose:
            print('nm')
        if srmodel is None:
            output_dict['NM'] = neuromelanin( nm_image_list, t1imgbrn, t1_image, hier['deep_cit168lab'], verbose=verbose )
        else:
            output_dict['NM'] = neuromelanin( nm_image_list, t1imgbrn, t1_image, hier['deep_cit168lab'], srmodel=srmodel, target_range=target_range, verbose=verbose  )
################################## do the dti .....
    if len(dw_image) > 0 :
        if verbose:
            print('dti-x')
        if len( dw_image ) == 1: # use T1 for distortion correction and brain extraction
            if verbose:
                print("We have only one DTI: " + str(len(dw_image)))
            dw_image = dw_image[0]
            btpB0, btpDW = get_average_dwi_b0(dw_image)
            initrig = ants.registration( btpDW, hier['brain_n4_dnz'], 'antsRegistrationSyNRepro[r]' )['fwdtransforms'][0]
            tempreg = ants.registration( btpDW, hier['brain_n4_dnz'], 'SyNOnly',
                syn_metric='CC', syn_sampling=2,
                reg_iterations=[50,50,20],
                multivariate_extras=[ [ "CC", btpB0, hier['brain_n4_dnz'], 1, 2 ]],
                initial_transform=initrig
                )
            mybxt = ants.threshold_image( ants.iMath(hier['brain_n4_dnz'], "Normalize" ), 0.001, 1 )
            btpDW = ants.apply_transforms( btpDW, btpDW,
                tempreg['invtransforms'][1], interpolator='linear')
            btpB0 = ants.apply_transforms( btpB0, btpB0,
                tempreg['invtransforms'][1], interpolator='linear')
            dwimask = ants.apply_transforms( btpDW, mybxt, tempreg['fwdtransforms'][1], interpolator='nearestNeighbor')
            # dwimask = ants.iMath(dwimask,'MD',1)
            t12dwi = ants.apply_transforms( btpDW, hier['brain_n4_dnz'], tempreg['fwdtransforms'][1], interpolator='linear')
            output_dict['DTI'] = joint_dti_recon(
                dw_image,
                bvals[0],
                bvecs[0],
                jhu_atlas=JHU_atlas,
                jhu_labels=JHU_labels,
                brain_mask = dwimask,
                reference_B0 = btpB0,
                reference_DWI = btpDW,
                srmodel=srmodel,
                motion_correct=dti_motion_correct, # set to False if using input from qsiprep
                denoise=dti_denoise,
                verbose = verbose)
        else :  # use phase encoding acquisitions for distortion correction and T1 for brain extraction
            if verbose:
                print("We have both DTI_LR and DTI_RL: " + str(len(dw_image)))
            a1b,a1w=get_average_dwi_b0(dw_image[0])
            a2b,a2w=get_average_dwi_b0(dw_image[1],fixed_b0=a1b,fixed_dwi=a1w)
            btpB0, btpDW = dti_template(
                b_image_list=[a1b,a2b],
                w_image_list=[a1w,a2w],
                iterations=7, verbose=verbose )
            initrig = ants.registration( btpDW, hier['brain_n4_dnz'], 'antsRegistrationSyNRepro[r]' )['fwdtransforms'][0]
            tempreg = ants.registration( btpDW, hier['brain_n4_dnz'], 'SyNOnly',
                syn_metric='CC', syn_sampling=2,
                reg_iterations=[50,50,20],
                multivariate_extras=[ [ "CC", btpB0, hier['brain_n4_dnz'], 1, 2 ]],
                initial_transform=initrig
                )
            mybxt = ants.threshold_image( ants.iMath(hier['brain_n4_dnz'], "Normalize" ), 0.001, 1 )
            dwimask = ants.apply_transforms( btpDW, mybxt, tempreg['fwdtransforms'], interpolator='nearestNeighbor')
            output_dict['DTI'] = joint_dti_recon(
                dw_image[0],
                bvals[0],
                bvecs[0],
                jhu_atlas=JHU_atlas,
                jhu_labels=JHU_labels,
                brain_mask = dwimask,
                reference_B0 = btpB0,
                reference_DWI = btpDW,
                srmodel=srmodel,
                img_RL=dw_image[1],
                bval_RL=bvals[1],
                bvec_RL=bvecs[1],
                motion_correct=dti_motion_correct, # set to False if using input from qsiprep
                denoise=dti_denoise,
                verbose = verbose)
        mydti = output_dict['DTI']
        # summarize dwi with T1 outputs
        # first - register ....
        reg = ants.registration( mydti['recon_fa'], hier['brain_n4_dnz'], 'antsRegistrationSyNRepro[s]', total_sigma=1.0 )
        ##################################################
        output_dict['FA_summ'] = hierarchical_modality_summary(
            mydti['recon_fa'],
            hier=hier,
            modality_name='fa',
            transformlist=reg['fwdtransforms'],
            verbose = False )
        ##################################################
        output_dict['MD_summ'] = hierarchical_modality_summary(
            mydti['recon_md'],
            hier=hier,
            modality_name='md',
            transformlist=reg['fwdtransforms'],
            verbose = False )
        # these inputs should come from nicely processed data
        dktmapped = ants.apply_transforms(
            mydti['recon_fa'],
            hier['dkt_parc']['dkt_cortex'],
            reg['fwdtransforms'], interpolator='nearestNeighbor' )
        citmapped = ants.apply_transforms(
            mydti['recon_fa'],
            hier['cit168lab'],
            reg['fwdtransforms'], interpolator='nearestNeighbor' )
        dktmapped[ citmapped > 0]=0
        mask = ants.threshold_image( mydti['recon_fa'], 0.01, 2.0 ).iMath("GetLargestComponent")
        if do_tractography: # dwi_deterministic_tracking dwi_closest_peak_tracking
            output_dict['tractography'] = dwi_deterministic_tracking(
                mydti['dwi_LR_dewarped'],
                mydti['recon_fa'],
                mydti['bval_LR'],
                mydti['bvec_LR'],
                seed_density = 1,
                mask=mask,
                verbose = verbose )
            mystr = output_dict['tractography']
            output_dict['tractography_connectivity'] = dwi_streamline_connectivity( mystr['streamlines'], dktmapped+citmapped, cnxcsv, verbose=verbose )
    ################################## do the flair .....
    if flair_image is not None:
        if verbose:
            print('flair')
        wmhprior = None
        priorfn = ex_path_mm + 'CIT168_wmhprior_700um_pad_adni.nii.gz'
        if ( exists( priorfn ) ):
            wmhprior = ants.image_read( priorfn )
            wmhprior = ants.apply_transforms( t1_image, wmhprior, do_normalization['invtransforms'] )
        output_dict['flair'] = boot_wmh( flair_image, t1_image, t1atropos,
            prior_probability=wmhprior, verbose=verbose )
    #################################################################
    ### NOTES: deforming to a common space and writing out images ###
    ### images we want come from: DTI, NM, rsf, thickness ###########
    #################################################################
    if do_normalization is not None:
        if verbose:
            print('normalization')
        # might reconsider this template space - cropped and/or higher res?
        # template = ants.resample_image( template, [1,1,1], use_voxels=False )
        # t1reg = ants.registration( template, hier['brain_n4_dnz'], "antsRegistrationSyNQuickRepro[s]")
        t1reg = do_normalization
        if do_kk:
            normalization_dict['kk_norm'] = ants.apply_transforms( group_template, output_dict['kk']['thickness_image'], group_transform )
        if output_dict['DTI'] is not None:
            mydti = output_dict['DTI']
            dtirig = ants.registration( hier['brain_n4_dnz'], mydti['recon_fa'], 'antsRegistrationSyNRepro[r]' )
            normalization_dict['MD_norm'] = ants.apply_transforms( group_template, mydti['recon_md'],group_transform+dtirig['fwdtransforms'] )
            normalization_dict['FA_norm'] = ants.apply_transforms( group_template, mydti['recon_fa'],group_transform+dtirig['fwdtransforms'] )
            output_directory = tempfile.mkdtemp()
            do_dti_norm=False
            if do_dti_norm:
                comptx = ants.apply_transforms( group_template, group_template, group_transform+dtirig['fwdtransforms'], compose = output_directory + '/xxx' )
                tspc=[2.,2.,2.]
                if srmodel is not None:
                    tspc=[1.,1.,1.]
                group_template2mm = ants.resample_image( group_template, tspc  )
                normalization_dict['DTI_norm'] = transform_and_reorient_dti( group_template2mm, mydti['dti'], comptx, verbose=False )
            import shutil
            shutil.rmtree(output_directory, ignore_errors=True )
        if output_dict['rsf'] is not None:
            if False:
                rsfpro = output_dict['rsf'] # FIXME
                rsfrig = ants.registration( hier['brain_n4_dnz'], rsfpro['meanBold'], 'antsRegistrationSyNRepro[r]' )
                for netid in get_antsimage_keys( rsfpro ):
                    rsfkey = netid + "_norm"
                    normalization_dict[rsfkey] = ants.apply_transforms(
                        group_template, rsfpro[netid],
                        group_transform+rsfrig['fwdtransforms'] )
        if output_dict['perf'] is not None: # zizzer
            comptx = group_transform + output_dict['perf']['t1reg']['invtransforms']
            normalization_dict['perf_norm'] = ants.apply_transforms( group_template,
                output_dict['perf']['perfusion'], comptx,
                whichtoinvert=[False,False,True,False] )
            normalization_dict['cbf_norm'] = ants.apply_transforms( group_template,
                output_dict['perf']['cbf'], comptx,
                whichtoinvert=[False,False,True,False] )
        if output_dict['pet3d'] is not None: # zizzer
            secondTx=output_dict['pet3d']['t1reg']['invtransforms']
            comptx = group_transform + secondTx
            if len( secondTx ) == 2:
                wti=[False,False,True,False]
            else:
                wti=[False,False,True]
            normalization_dict['pet3d_norm'] = ants.apply_transforms( group_template,
                output_dict['pet3d']['pet3d'], comptx,
                whichtoinvert=wti )
        if nm_image_list is not None:
            nmpro = output_dict['NM']
            nmrig = nmpro['t1_to_NM_transform'] # this is an inverse tx
            normalization_dict['NM_norm'] = ants.apply_transforms( group_template, nmpro['NM_avg'], group_transform+nmrig,
                whichtoinvert=[False,False,True])

    if verbose:
        print('mm done')
    return output_dict, normalization_dict


def mm_nrg(
    studyid,   # pandas data frame
    sourcedir = os.path.expanduser( "~/data/PPMI/MV/example_s3_b/images/PPMI/" ),
    sourcedatafoldername = 'images', # root for source data
    processDir = "processed", # where output will go - parallel to sourcedatafoldername
    mysep = '-', # define a separator for filename components
    srmodel_T1 = False, # optional - will add a great deal of time
    srmodel_NM = False, # optional - will add a great deal of time
    srmodel_DTI = False, # optional - will add a great deal of time
    visualize = True,
    nrg_modality_list = ["T1w", "NM2DMT", "DTI","T2Flair", "rsfMRI" ],
    verbose = True
):
    """
    too dangerous to document ... use with care.

    processes multiple modality MRI specifically:

    * T1w
    * T2Flair
    * DTI, DTI_LR, DTI_RL
    * rsfMRI, rsfMRI_LR, rsfMRI_RL
    * NM2DMT (neuromelanin)

    other modalities may be added later ...

    "trust me, i know what i'm doing" - sledgehammer

    convert to pynb via:
        p2j mm.py -o

    convert the ipynb to html via:
        jupyter nbconvert ANTsPyMM/tests/mm.ipynb --execute --to html

    this function assumes NRG format for the input data ....
    we also assume that t1w hierarchical (if already done) was written
    via its standardized write function.
    NRG = https://github.com/stnava/biomedicalDataOrganization

    this function is verbose

    Parameters
    -------------

    studyid : must have columns 1. subjectID 2. date (in form 20220228) and 3. imageID
        other relevant columns include nmid1-10, rsfid1, rsfid2, dtid1, dtid2, flairid;
        these provide unique image IDs for these modalities: nm=neuromelanin, dti=diffusion tensor,
        rsf=resting state fmri, flair=T2Flair.  none of these are required. only
        t1 is required.  rsfid1/rsfid2 will be processed jointly. same for dtid1/dtid2 and nmid*.  see antspymm.generate_mm_dataframe

    sourcedir : a study specific folder containing individual subject folders

    sourcedatafoldername : root for source data e.g. "images"

    processDir : where output will go - parallel to sourcedatafoldername e.g.
        "processed"

    mysep : define a character separator for filename components

    srmodel_T1 : False (default) - will add a great deal of time - or h5 filename, 2 chan

    srmodel_NM : False (default) - will add a great deal of time - or h5 filename, 1 chan

    srmodel_DTI : False (default) - will add a great deal of time - or h5 filename, 1 chan

    visualize : True - will plot some results to png

    nrg_modality_list : list of permissible modalities - always include [T1w] as base

    verbose : boolean

    Returns
    ---------

    writes output to disk and potentially produces figures that may be
    captured in a ipynb / html file.

    """
    studyid = studyid.dropna(axis=1)
    if studyid.shape[0] < 1:
        raise ValueError('studyid has no rows')
    musthavecols = ['subjectID','date','imageID']
    for k in range(len(musthavecols)):
        if not musthavecols[k] in studyid.keys():
            raise ValueError('studyid is missing column ' +musthavecols[k] )
    import glob as glob
    from os.path import exists
    ex_path = os.path.expanduser( "~/.antspyt1w/" )
    ex_pathmm = os.path.expanduser( "~/.antspymm/" )
    templatefn = ex_path + 'CIT168_T1w_700um_pad_adni.nii.gz'
    if not exists( templatefn ):
        print( "**missing files** => call get_data from latest antspyt1w and antspymm." )
        antspyt1w.get_data( force_download=True )
        get_data( force_download=True )
    temp = sourcedir.split( "/" )
    splitCount = len( temp )
    template = mm_read( templatefn ) # Read in template
    test_run = False
    if test_run:
        visualize=False
    # get sid and dtid from studyid
    sid = str(studyid['subjectID'].iloc[0])
    dtid = str(studyid['date'].iloc[0])
    iid = str(studyid['imageID'].iloc[0])
    subjectrootpath = os.path.join(sourcedir,sid, dtid)
    if verbose:
        print("subjectrootpath: "+ subjectrootpath )
    myimgsInput = glob.glob( subjectrootpath+"/*" )
    myimgsInput.sort( )
    if verbose:
        print( myimgsInput )
    # hierarchical
    # NOTE: if there are multiple T1s for this time point, should take
    # the one with the highest resnetGrade
    t1_search_path = os.path.join(subjectrootpath, "T1w", iid, "*nii.gz")
    if verbose:
        print(f"t1 search path: {t1_search_path}")
    t1fn = glob.glob(t1_search_path)
    t1fn.sort()
    if len( t1fn ) < 1:
        raise ValueError('mm_nrg cannot find the T1w with uid ' + iid + ' @ ' + subjectrootpath )
    t1fn = t1fn[0]
    t1 = mm_read( t1fn )
    hierfn0 = re.sub( sourcedatafoldername, processDir, t1fn)
    hierfn0 = re.sub( ".nii.gz", "", hierfn0)
    hierfn = re.sub( "T1w", "T1wHierarchical", hierfn0)
    hierfn = hierfn + mysep
    hierfntest = hierfn + 'snseg.csv'
    regout = hierfn0 + mysep + "syn"
    templateTx = {
        'fwdtransforms': [ regout+'1Warp.nii.gz', regout+'0GenericAffine.mat'],
        'invtransforms': [ regout+'0GenericAffine.mat', regout+'1InverseWarp.nii.gz']  }
    if verbose:
        print( "-<REGISTRATION EXISTENCE>-: \n" + 
              "NAMING: " + regout+'0GenericAffine.mat' + " \n " +
            str(exists( templateTx['fwdtransforms'][0])) + " " +
            str(exists( templateTx['fwdtransforms'][1])) + " " +
            str(exists( templateTx['invtransforms'][0])) + " " +
            str(exists( templateTx['invtransforms'][1])) )
    if verbose:
        print( hierfntest )
    hierexists = exists( hierfntest ) # FIXME should test this explicitly but we assume it here
    hier = None
    if not hierexists and not testloop:
        subjectpropath = os.path.dirname( hierfn )
        if verbose:
            print( subjectpropath )
        os.makedirs( subjectpropath, exist_ok=True  )
        hier = antspyt1w.hierarchical( t1, hierfn, labels_to_register=None )
        antspyt1w.write_hierarchical( hier, hierfn )
        t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                hier['dataframes'], identifier=None )
        t1wide.to_csv( hierfn + 'mmwide.csv' )
    ################# read the hierarchical data ###############################
    hier = antspyt1w.read_hierarchical( hierfn )
    if exists( hierfn + 'mmwide.csv' ) :
        t1wide = pd.read_csv( hierfn + 'mmwide.csv' )
    elif not testloop:
        t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                hier['dataframes'], identifier=None )
    if srmodel_T1 is not None :
        hierfnSR = re.sub( sourcedatafoldername, processDir, t1fn)
        hierfnSR = re.sub( "T1w", "T1wHierarchicalSR", hierfnSR)
        hierfnSR = re.sub( ".nii.gz", "", hierfnSR)
        hierfnSR = hierfnSR + mysep
        hierfntest = hierfnSR + 'mtl.csv'
        if verbose:
            print( hierfntest )
        hierexists = exists( hierfntest ) # FIXME should test this explicitly but we assume it here
        if not hierexists:
            subjectpropath = os.path.dirname( hierfnSR )
            if verbose:
                print( subjectpropath )
            os.makedirs( subjectpropath, exist_ok=True  )
            # hierarchical_to_sr(t1hier, sr_model, tissue_sr=False, blending=0.5, verbose=False)
            bestup = siq.optimize_upsampling_shape( ants.get_spacing(t1), modality='T1' )
            mdlfn = re.sub( 'bestup', bestup, srmodel_T1 ) 
            if verbose:
                print( mdlfn )
            if exists( mdlfn ):
                srmodel_T1_mdl = tf.keras.models.load_model( mdlfn, compile=False )
            else:
                print( mdlfn + " does not exist - will not run.")
            hierSR = antspyt1w.hierarchical_to_sr( hier, srmodel_T1_mdl, blending=None, tissue_sr=False )
            antspyt1w.write_hierarchical( hierSR, hierfnSR )
            t1wideSR = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                    hierSR['dataframes'], identifier=None )
            t1wideSR.to_csv( hierfnSR + 'mmwide.csv' )
    hier = antspyt1w.read_hierarchical( hierfn )
    if exists( hierfn + 'mmwide.csv' ) :
        t1wide = pd.read_csv( hierfn + 'mmwide.csv' )
    elif not testloop:
        t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                hier['dataframes'], identifier=None )
    if not testloop:
        t1imgbrn = hier['brain_n4_dnz']
        t1atropos = hier['dkt_parc']['tissue_segmentation']
    # loop over modalities and then unique image IDs
    # we treat NM in a "special" way -- aggregating repeats
    # other modalities (beyond T1) are treated individually
    nimages = len(myimgsInput)
    if verbose:
        print(  " we have : " + str(nimages) + " modalities.")
    for overmodX in nrg_modality_list:
        counter=counter+1
        if counter > (len(nrg_modality_list)+1):
            print("This is weird. " + str(counter))
            return
        if overmodX == 'T1w':
            iidOtherMod = iid
            mod_search_path = os.path.join(subjectrootpath, overmodX, iidOtherMod, "*nii.gz")
            myimgsr = glob.glob(mod_search_path)
        elif overmodX == 'NM2DMT' and ('nmid1' in studyid.keys() ):
            iidOtherMod = str( int(studyid['nmid1'].iloc[0]) )
            mod_search_path = os.path.join(subjectrootpath, overmodX, iidOtherMod, "*nii.gz")
            myimgsr = glob.glob(mod_search_path)
            for nmnum in range(2,11):
                locnmnum = 'nmid'+str(nmnum)
                if locnmnum in studyid.keys() :
                    iidOtherMod = str( int(studyid[locnmnum].iloc[0]) )
                    mod_search_path = os.path.join(subjectrootpath, overmodX, iidOtherMod, "*nii.gz")
                    myimgsr.append( glob.glob(mod_search_path)[0] )
        elif 'rsfMRI' in overmodX and ( ( 'rsfid1' in studyid.keys() ) or ('rsfid2' in studyid.keys() ) ):
            myimgsr = []
            if  'rsfid1' in studyid.keys():
                iidOtherMod = str( int(studyid['rsfid1'].iloc[0]) )
                mod_search_path = os.path.join(subjectrootpath, overmodX+"*", iidOtherMod, "*nii.gz")
                myimgsr.append( glob.glob(mod_search_path)[0] )
            if  'rsfid2' in studyid.keys():
                iidOtherMod = str( int(studyid['rsfid2'].iloc[0]) )
                mod_search_path = os.path.join(subjectrootpath, overmodX+"*", iidOtherMod, "*nii.gz")
                myimgsr.append( glob.glob(mod_search_path)[0] )
        elif 'DTI' in overmodX and (  'dtid1' in studyid.keys() or  'dtid2' in studyid.keys() ):
            myimgsr = []
            if  'dtid1' in studyid.keys():
                iidOtherMod = str( int(studyid['dtid1'].iloc[0]) )
                mod_search_path = os.path.join(subjectrootpath, overmodX+"*", iidOtherMod, "*nii.gz")
                myimgsr.append( glob.glob(mod_search_path)[0] )
            if  'dtid2' in studyid.keys():
                iidOtherMod = str( int(studyid['dtid2'].iloc[0]) )
                mod_search_path = os.path.join(subjectrootpath, overmodX+"*", iidOtherMod, "*nii.gz")
                myimgsr.append( glob.glob(mod_search_path)[0] )
        elif 'T2Flair' in overmodX and ('flairid' in studyid.keys() ):
            iidOtherMod = str( int(studyid['flairid'].iloc[0]) )
            mod_search_path = os.path.join(subjectrootpath, overmodX, iidOtherMod, "*nii.gz")
            myimgsr = glob.glob(mod_search_path)
        if verbose:
            print( "overmod " + overmodX + " " + iidOtherMod )
            print(f"modality search path: {mod_search_path}")
        myimgsr.sort()
        if len(myimgsr) > 0:
            overmodXx = str(overmodX)
            dowrite=False
            if verbose:
                print( 'overmodX is : ' + overmodXx )
                print( 'example image name is : '  )
                print( myimgsr )
            if overmodXx == 'NM2DMT':
                myimgsr2 = myimgsr
                myimgsr2.sort()
                is4d = False
                temp = ants.image_read( myimgsr2[0] )
                if temp.dimension == 4:
                    is4d = True
                if len( myimgsr2 ) == 1 and not is4d: # check dimension
                    myimgsr2 = myimgsr2 + myimgsr2
                subjectpropath = os.path.dirname( myimgsr2[0] )
                subjectpropath = re.sub( sourcedatafoldername, processDir,subjectpropath )
                if verbose:
                    print( "subjectpropath " + subjectpropath )
                mysplit = subjectpropath.split( "/" )
                os.makedirs( subjectpropath, exist_ok=True  )
                mysplitCount = len( mysplit )
                project = mysplit[mysplitCount-5]
                subject = mysplit[mysplitCount-4]
                date = mysplit[mysplitCount-3]
                modality = mysplit[mysplitCount-2]
                uider = mysplit[mysplitCount-1]
                identifier = mysep.join([project, subject, date, modality ])
                identifier = identifier + "_" + iid
                mymm = subjectpropath + "/" + identifier
                mymmout = makewideout( mymm )
                if verbose and not exists( mymmout ):
                    print( "NM " + mymm  + ' execution ')
                elif verbose and exists( mymmout ) :
                    print( "NM " + mymm + ' complete ' )
                if exists( mymmout ):
                    continue
                if is4d:
                    nmlist = ants.ndimage_to_list( mm_read( myimgsr2[0] ) )
                else:
                    nmlist = []
                    for zz in myimgsr2:
                        nmlist.append( mm_read( zz ) )
                srmodel_NM_mdl = None
                if srmodel_NM is not None:
                    bestup = siq.optimize_upsampling_shape( ants.get_spacing(nmlist[0]), modality='NM', roundit=True )
                    if isinstance( srmodel_NM, str ):
                        mdlfn = re.sub( "bestup", bestup, srmodel_NM )
                    if exists( mdlfn ):
                        if verbose:
                            print(mdlfn)
                        srmodel_NM_mdl = tf.keras.models.load_model( mdlfn, compile=False  )
                    else:
                        print( mdlfn + " does not exist - wont use SR")
                if not testloop:
                    tabPro, normPro = mm( t1, hier,
                            nm_image_list = nmlist,
                            srmodel=srmodel_NM_mdl,
                            do_tractography=False,
                            do_kk=False,
                            do_normalization=templateTx,
                            test_run=test_run,
                            verbose=True )
                    if not test_run:
                        write_mm( output_prefix=mymm, mm=tabPro, mm_norm=normPro, t1wide=None, separator=mysep )
                        nmpro = tabPro['NM']
                        mysl = range( nmpro['NM_avg'].shape[2] )
                    if visualize:
                        mysl = range( nmpro['NM_avg'].shape[2] )
                        ants.plot( nmpro['NM_avg'],  nmpro['t1_to_NM'], slices=mysl, axis=2, title='nm + t1', filename=mymm+mysep+"NMavg.png" )
                        mysl = range( nmpro['NM_avg_cropped'].shape[2] )
                        ants.plot( nmpro['NM_avg_cropped'], axis=2, slices=mysl, overlay_alpha=0.3, title='nm crop', filename=mymm+mysep+"NMavgcrop.png" )
                        ants.plot( nmpro['NM_avg_cropped'], nmpro['t1_to_NM'], axis=2, slices=mysl, overlay_alpha=0.3, title='nm crop + t1', filename=mymm+mysep+"NMavgcropt1.png" )
                        ants.plot( nmpro['NM_avg_cropped'], nmpro['NM_labels'], axis=2, slices=mysl, title='nm crop + labels', filename=mymm+mysep+"NMavgcroplabels.png" )
            else :
                if len( myimgsr ) > 0:
                    dowrite=False
                    myimgcount = 0
                    if len( myimgsr ) > 0 :
                        myimg = myimgsr[myimgcount]
                        subjectpropath = os.path.dirname( myimg )
                        subjectpropath = re.sub( sourcedatafoldername, processDir, subjectpropath )
                        mysplit = subjectpropath.split("/")
                        mysplitCount = len( mysplit )
                        project = mysplit[mysplitCount-5]
                        date = mysplit[mysplitCount-4]
                        subject = mysplit[mysplitCount-3]
                        mymod = mysplit[mysplitCount-2] # FIXME system dependent
                        uid = mysplit[mysplitCount-1] # unique image id
                        os.makedirs( subjectpropath, exist_ok=True  )
                        if mymod == 'T1w':
                            identifier = mysep.join([project, date, subject, mymod, uid])
                        else:  # add the T1 unique id since that drives a lot of the analysis
                            identifier = mysep.join([project, date, subject, mymod, uid ])
                            identifier = identifier + "_" + iid
                        mymm = subjectpropath + "/" + identifier
                        mymmout = makewideout( mymm )
                        if verbose and not exists( mymmout ):
                            print("Modality specific processing: " + mymod + " execution " )
                            print( mymm )
                        elif verbose and exists( mymmout ) :
                            print("Modality specific processing: " + mymod + " complete " )
                        if exists( mymmout ) :
                            continue
                        if verbose:
                            print(subjectpropath)
                            print(identifier)
                            print( myimg )
                        if not testloop:
                            img = mm_read( myimg )
                            ishapelen = len( img.shape )
                            if mymod == 'T1w' and ishapelen == 3: # for a real run, set to True
                                if not exists( regout + "logjacobian.nii.gz" ) or not exists( regout+'1Warp.nii.gz' ):
                                    if verbose:
                                        print('start t1 registration')
                                    ex_path = os.path.expanduser( "~/.antspyt1w/" )
                                    templatefn = ex_path + 'CIT168_T1w_700um_pad_adni.nii.gz'
                                    template = mm_read( templatefn )
                                    template = ants.resample_image( template, [1,1,1], use_voxels=False )
                                    t1reg = ants.registration( template, hier['brain_n4_dnz'],
                                        "antsRegistrationSyNQuickRepro[s]", outprefix = regout, verbose=False )
                                    myjac = ants.create_jacobian_determinant_image( template,
                                        t1reg['fwdtransforms'][0], do_log=True, geom=True )
                                    image_write_with_thumbnail( myjac, regout + "logjacobian.nii.gz", thumb=False )
                                    if visualize:
                                        ants.plot( ants.iMath(t1reg['warpedmovout'],"Normalize"),  axis=2, nslices=21, ncol=7, crop=True, title='warped to template', filename=regout+"totemplate.png" )
                                        ants.plot( ants.iMath(myjac,"Normalize"),  axis=2, nslices=21, ncol=7, crop=True, title='jacobian', filename=regout+"jacobian.png" )
                                if not exists( mymm + mysep + "kk_norm.nii.gz" ):
                                    dowrite=True
                                    if verbose:
                                        print('start kk')
                                    tabPro, normPro = mm( t1, hier,
                                        srmodel=None,
                                        do_tractography=False,
                                        do_kk=True,
                                        do_normalization=templateTx,
                                        test_run=test_run,
                                        verbose=True )
                                    if visualize:
                                        maxslice = np.min( [21, hier['brain_n4_dnz'].shape[2] ] )
                                        ants.plot( hier['brain_n4_dnz'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='brain extraction', filename=mymm+mysep+"brainextraction.png" )
                                        ants.plot( tabPro['kk']['thickness_image'], axis=2, nslices=maxslice, ncol=7, crop=True, title='kk',
                                        cmap='plasma', filename=mymm+mysep+"kkthickness.png" )
                            if mymod == 'T2Flair' and ishapelen == 3:
                                dowrite=True
                                tabPro, normPro = mm( t1, hier,
                                    flair_image = img,
                                    srmodel=None,
                                    do_tractography=False,
                                    do_kk=False,
                                    do_normalization=templateTx,
                                    test_run=test_run,
                                    verbose=True )
                                if visualize:
                                    maxslice = np.min( [21, img.shape[2] ] )
                                    ants.plot_ortho( img, crop=True, title='Flair', filename=mymm+mysep+"flair.png", flat=True )
                                    ants.plot_ortho( img, tabPro['flair']['WMH_probability_map'], crop=True, title='Flair + WMH', filename=mymm+mysep+"flairWMH.png", flat=True )
                                    if tabPro['flair']['WMH_posterior_probability_map'] is not None:
                                        ants.plot_ortho( img, tabPro['flair']['WMH_posterior_probability_map'],  crop=True, title='Flair + prior WMH', filename=mymm+mysep+"flairpriorWMH.png", flat=True )
                            if ( mymod == 'rsfMRI_LR' or mymod == 'rsfMRI_RL' or mymod == 'rsfMRI' )  and ishapelen == 4:
                                img2 = None
                                if len( myimgsr ) > 1:
                                    img2 = mm_read( myimgsr[myimgcount+1] )
                                    ishapelen2 = len( img2.shape )
                                    if ishapelen2 != 4 :
                                        img2 = None
                                dowrite=True
                                tabPro, normPro = mm( t1, hier,
                                    rsf_image=[img,img2],
                                    srmodel=None,
                                    do_tractography=False,
                                    do_kk=False,
                                    do_normalization=templateTx,
                                    test_run=test_run,
                                    verbose=True )
                                if tabPro['rsf'] is not None and visualize:
                                    dfn=tabPro['rsf']['dfnname']
                                    maxslice = np.min( [21, tabPro['rsf']['meanBold'].shape[2] ] )
                                    ants.plot( tabPro['rsf']['meanBold'],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='meanBOLD', filename=mymm+mysep+"meanBOLD.png" )
                                    ants.plot( tabPro['rsf']['meanBold'], ants.iMath(tabPro['rsf']['alff'],"Normalize"),
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='ALFF', filename=mymm+mysep+"boldALFF.png" )
                                    ants.plot( tabPro['rsf']['meanBold'], ants.iMath(tabPro['rsf']['falff'],"Normalize"),
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='fALFF', filename=mymm+mysep+"boldfALFF.png" )
                                    ants.plot( tabPro['rsf']['meanBold'], tabPro['rsf'][dfn],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='DefaultMode', filename=mymm+mysep+"boldDefaultMode.png" )
                            if ( mymod == 'DTI_LR' or mymod == 'DTI_RL' or mymod == 'DTI' ) and ishapelen == 4:
                                dowrite=True
                                bvalfn = re.sub( '.nii.gz', '.bval' , myimg )
                                bvecfn = re.sub( '.nii.gz', '.bvec' , myimg )
                                imgList = [ img ]
                                bvalfnList = [ bvalfn ]
                                bvecfnList = [ bvecfn ]
                                if len( myimgsr ) > 1:  # find DTI_RL
                                    dtilrfn = myimgsr[myimgcount+1]
                                    if len( dtilrfn ) == 1:
                                        bvalfnRL = re.sub( '.nii.gz', '.bval' , dtilrfn )
                                        bvecfnRL = re.sub( '.nii.gz', '.bvec' , dtilrfn )
                                        imgRL = ants.image_read( dtilrfn )
                                        imgList.append( imgRL )
                                        bvalfnList.append( bvalfnRL )
                                        bvecfnList.append( bvecfnRL )
                                srmodel_DTI_mdl=None
                                if srmodel_DTI is not None:
                                    temp = ants.get_spacing(img)
                                    dtspc=[temp[0],temp[1],temp[2]]
                                    bestup = siq.optimize_upsampling_shape( dtspc, modality='DTI' )
                                    if isinstance( srmodel_DTI, str ):
                                        mdlfn = re.sub( "bestup", bestup, srmodel_DTI )
                                    if exists( mdlfn ):
                                        if verbose:
                                            print(mdlfn)
                                        srmodel_DTI_mdl = tf.keras.models.load_model( mdlfn, compile=False )
                                    else:
                                        print(mdlfn + " does not exist - wont use SR")
                                tabPro, normPro = mm( t1, hier,
                                    dw_image=imgList,
                                    bvals = bvalfnList,
                                    bvecs = bvecfnList,
                                    srmodel=srmodel_DTI_mdl,
                                    do_tractography=not test_run,
                                    do_kk=False,
                                    do_normalization=templateTx,
                                    test_run=test_run,
                                    verbose=True )
                                mydti = tabPro['DTI']
                                if visualize:
                                    maxslice = np.min( [21, mydti['recon_fa'] ] )
                                    ants.plot( mydti['recon_fa'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='FA', filename=mymm+mysep+"FAbetter.png"  )
                                    ants.plot( mydti['recon_fa'], mydti['jhu_labels'], axis=2, nslices=maxslice, ncol=7, crop=True, title='FA + JHU', filename=mymm+mysep+"FAJHU.png"  )
                                    ants.plot( mydti['recon_md'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='MD', filename=mymm+mysep+"MD.png"  )
                            if dowrite:
                                write_mm( output_prefix=mymm, mm=tabPro, mm_norm=normPro, t1wide=t1wide, separator=mysep, verbose=True )
                                for mykey in normPro.keys():
                                    if normPro[mykey] is not None:
                                        if visualize and normPro[mykey].components == 1 and False:
                                            ants.plot( template, normPro[mykey], axis=2, nslices=21, ncol=7, crop=True, title=mykey, filename=mymm+mysep+mykey+".png"   )
        if overmodX == nrg_modality_list[ len( nrg_modality_list ) - 1 ]:
            return
        if verbose:
            print("done with " + overmodX )
    if verbose:
        print("mm_nrg complete.")
    return



def mm_csv(
    studycsv,   # pandas data frame
    mysep = '-', # or "_" for BIDS
    srmodel_T1 = False, # optional - will add a great deal of time
    srmodel_NM = False, # optional - will add a great deal of time
    srmodel_DTI = False, # optional - will add a great deal of time
    dti_motion_correct = 'antsRegistrationSyNQuickRepro[r]',
    dti_denoise = False,
    nrg_modality_list = None,
    normalization_template = None,
    normalization_template_output = None,
    normalization_template_transform_type = "antsRegistrationSyNRepro[s]",
    normalization_template_spacing=None,
    enantiomorphic=False,
    perfusion_trim = 10,
    perfusion_m0_image = None,
    perfusion_m0 = None,
    rsf_upsampling = 3.0,
    pet3d = None,
    min_t1_spacing_for_sr = 0.8,
):
    """
    too dangerous to document ... use with care.

    processes multiple modality MRI specifically:

    * T1w
    * T2Flair
    * DTI, DTI_LR, DTI_RL
    * rsfMRI, rsfMRI_LR, rsfMRI_RL
    * NM2DMT (neuromelanin)

    other modalities may be added later ...

    "trust me, i know what i'm doing" - sledgehammer

    convert to pynb via:
        p2j mm.py -o

    convert the ipynb to html via:
        jupyter nbconvert ANTsPyMM/tests/mm.ipynb --execute --to html

    this function does not assume NRG format for the input data ....

    Parameters
    -------------

    studycsv : must have columns:
        - subjectID
        - date or session
        - imageID
        - modality
        - sourcedir
        - outputdir
        - filename (path to the t1 image)
        other relevant columns include nmid1-10, rsfid1, rsfid2, dtid1, dtid2, flairid;
        these provide filenames for these modalities: nm=neuromelanin, dti=diffusion tensor,
        rsf=resting state fmri, flair=T2Flair.  none of these are required. only
        t1 is required. rsfid1/rsfid2 will be processed jointly. same for dtid1/dtid2 and nmid*.
        see antspymm.generate_mm_dataframe

    sourcedir : a study specific folder containing individual subject folders

    outputdir : a study specific folder where individual output subject folders will go

    filename : the raw image filename (full path)

    srmodel_T1 : None (default) - .keras or h5 filename for SR model (siq generated). 

    srmodel_NM : None (default) - .keras or h5 filename for SR model (siq generated)
    the model name should follow a style like prefix_bestup_postfix where bestup will be replaced with an optimal upsampling factor eg 2x2x2 based on the data.  see siq.optimize_upsampling_shape.

    srmodel_DTI : None (default) - .keras or h5 filename for SR model (siq generated). 
    the model name should follow a style like prefix_bestup_postfix where bestup will be replaced with an optimal upsampling factor eg 2x2x2 based on the data.  see siq.optimize_upsampling_shape.

    dti_motion_correct : None, Rigid or SyN

    dti_denoise : boolean

    nrg_modality_list : optional; defaults to None; use to focus on a given modality

    normalization_template : optional; defaults to None; if present, all images will
        be deformed into this space and the deformation will be stored with an extension
        related to this variable.  this should be a brain extracted T1w image.

    normalization_template_output : optional string; defaults to None; naming for the 
        normalization_template outputs which will be in the T1w directory.

    normalization_template_transform_type : optional string transform type passed to ants.registration

    normalization_template_spacing : 3-tuple controlling the resolution at which registration is computed 
    
    enantiomorphic: boolean (WIP)

    perfusion_trim : optional integer number of time volumes to exclude from the front of the perfusion time series

    perfusion_m0_image : optional m0 antsImage associated with the perfusion time series

    perfusion_m0 : optional list containing indices of the m0 in the perfusion time series

    rsf_upsampling : optional upsampling parameter value in mm; if set to zero, no upsampling is done

    pet3d : optional antsImage for PET (or other 3d scalar) data which we want to summarize

    min_t1_spacing_for_sr : float 
        if the minimum input image spacing is less than this value, 
        the function will return the original image.  Default 0.8.

    Returns
    ---------

    writes output to disk and produces figures

    """
    import traceback
    visualize = True
    verbose = True
    if verbose:
        print( version() )
    if nrg_modality_list is None:
        nrg_modality_list = get_valid_modalities()
    if studycsv.shape[0] < 1:
        raise ValueError('studycsv has no rows')
    musthavecols = ['projectID', 'subjectID','date','imageID','modality','sourcedir','outputdir','filename']
    for k in range(len(musthavecols)):
        if not musthavecols[k] in studycsv.keys():
            raise ValueError('studycsv is missing column ' +musthavecols[k] )
    import glob as glob
    from os.path import exists
    ex_path = os.path.expanduser( "~/.antspyt1w/" )
    ex_pathmm = os.path.expanduser( "~/.antspymm/" )
    templatefn = ex_path + 'CIT168_T1w_700um_pad_adni.nii.gz'
    if not exists( templatefn ):
        print( "**missing files** => call get_data from latest antspyt1w and antspymm." )
        antspyt1w.get_data( force_download=True )
        get_data( force_download=True )
    template = mm_read( templatefn ) # Read in template
    test_run = False
    if test_run:
        visualize=False
    # get sid and dtid from studycsv
    # musthavecols = ['projectID','subjectID','date','imageID','modality','sourcedir','outputdir','filename']
    projid = str(studycsv['projectID'].iloc[0])
    sid = str(studycsv['subjectID'].iloc[0])
    dtid = str(studycsv['date'].iloc[0])
    iid = str(studycsv['imageID'].iloc[0])
    t1iidUse=iid
    modality = str(studycsv['modality'].iloc[0])
    sourcedir = str(studycsv['sourcedir'].iloc[0])
    outputdir = str(studycsv['outputdir'].iloc[0])
    filename = str(studycsv['filename'].iloc[0])
    if not exists(filename):
            raise ValueError('mm_nrg cannot find filename ' + filename + ' in mm_csv' )

    # hierarchical
    # NOTE: if there are multiple T1s for this time point, should take
    # the one with the highest resnetGrade
    t1fn = filename
    if not exists( t1fn ):
        raise ValueError('mm_nrg cannot find the T1w with uid ' + t1fn )
    t1 = mm_read( t1fn, modality='T1w' )
    minspc = np.min(ants.get_spacing(t1))
    minshape = np.min(t1.shape)
    if minspc < 1e-16:
        warnings.warn('minimum spacing in T1w is too small - cannot process. ' + str(minspc) )
        return
    if minshape < 32:
        warnings.warn('minimum shape in T1w is too small - cannot process. ' + str(minshape) )
        return

    if enantiomorphic:
        t1 = enantiomorphic_filling_without_mask( t1, axis=0 )[0]
    hierfn = outputdir + "/"  + projid + "/" + sid + "/" + dtid + "/" + "T1wHierarchical" + '/' + iid + "/" + projid + mysep + sid + mysep + dtid + mysep + "T1wHierarchical" + mysep + iid + mysep
    hierfnSR = outputdir + "/" + projid + "/"  + sid + "/" + dtid + "/" + "T1wHierarchicalSR" + '/' + iid + "/" + projid + mysep + sid + mysep + dtid + mysep + "T1wHierarchicalSR" + mysep + iid + mysep
    hierfntest = hierfn + 'cerebellum.csv'
    if verbose:
        print( hierfntest )
    regout = re.sub("T1wHierarchical","T1w",hierfn) + "syn"
    templateTx = {
        'fwdtransforms': [ regout+'1Warp.nii.gz', regout+'0GenericAffine.mat'],
        'invtransforms': [ regout+'0GenericAffine.mat', regout+'1InverseWarp.nii.gz']  }
    groupTx = None
    # make the T1w directory
    os.makedirs( os.path.dirname(re.sub("T1wHierarchical","T1w",hierfn)), exist_ok=True  )
    if normalization_template_output is not None:
        normout = re.sub("T1wHierarchical","T1w",hierfn) +  normalization_template_output
        templateNormTx = {
            'fwdtransforms': [ normout+'1Warp.nii.gz', normout+'0GenericAffine.mat'],
            'invtransforms': [ normout+'0GenericAffine.mat', normout+'1InverseWarp.nii.gz']  }
        groupTx = templateNormTx['fwdtransforms']
    if verbose:
        print( "-<REGISTRATION EXISTENCE>-: \n" + 
              "NAMING: " + regout+'0GenericAffine.mat' + " \n " +
            str(exists( templateTx['fwdtransforms'][0])) + " " +
            str(exists( templateTx['fwdtransforms'][1])) + " " +
            str(exists( templateTx['invtransforms'][0])) + " " +
            str(exists( templateTx['invtransforms'][1])) )
    if verbose:
        print( hierfntest )
    hierexists = exists( hierfntest ) and exists( templateTx['fwdtransforms'][0]) and exists( templateTx['fwdtransforms'][1]) and exists( templateTx['invtransforms'][0]) and exists( templateTx['invtransforms'][1])
    hier = None
    if srmodel_T1 is not None:
        srmodel_T1_mdl = tf.keras.models.load_model( srmodel_T1, compile=False )
        if verbose:
            print("Convert T1w to SR via model ", srmodel_T1 )
        t1 = t1w_super_resolution_with_hemispheres( t1, srmodel_T1_mdl,
            min_spacing=min_t1_spacing_for_sr )
    if not hierexists and not testloop:
        subjectpropath = os.path.dirname( hierfn )
        if verbose:
            print( subjectpropath )
        os.makedirs( subjectpropath, exist_ok=True  )
        ants.image_write( t1, hierfn + 'head.nii.gz' )
        hier = antspyt1w.hierarchical( t1, hierfn, labels_to_register=None )
        antspyt1w.write_hierarchical( hier, hierfn )
        t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                hier['dataframes'], identifier=None )
        t1wide.to_csv( hierfn + 'mmwide.csv' )
    ################# read the hierarchical data ###############################
    # over-write the rbp data with a consistent and recent approach ############
    redograding = True
    if redograding:
        myx = antspyt1w.inspect_raw_t1( 
            ants.image_read(t1fn), hierfn + 'rbp' , option='both' )
        myx['brain'].to_csv( hierfn + 'rbp.csv', index=False )
        myx['brain'].to_csv( hierfn + 'rbpbrain.csv', index=False )
        del myx

    hier = antspyt1w.read_hierarchical( hierfn )
    t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
        hier['dataframes'], identifier=None )
    rgrade = str( t1wide['resnetGrade'].iloc[0] )
    if t1wide['resnetGrade'].iloc[0] < 0.20:
        warnings.warn('T1w quality check indicates failure: ' + rgrade + " will not process." )
        return
    else:
        print('T1w quality check indicates success: ' + rgrade + " will process." )

    if srmodel_T1 is not None and False : # deprecated
        hierfntest = hierfnSR + 'mtl.csv'
        if verbose:
            print( hierfntest )
        hierexists = exists( hierfntest ) # FIXME should test this explicitly but we assume it here
        if not hierexists:
            subjectpropath = os.path.dirname( hierfnSR )
            if verbose:
                print( subjectpropath )
            os.makedirs( subjectpropath, exist_ok=True  )
            # hierarchical_to_sr(t1hier, sr_model, tissue_sr=False, blending=0.5, verbose=False)
            bestup = siq.optimize_upsampling_shape( ants.get_spacing(t1), modality='T1' )
            if isinstance( srmodel_T1, str ):
                mdlfn = re.sub( 'bestup', bestup, srmodel_T1 )
            if verbose:
                print( mdlfn )
            if exists( mdlfn ):
                srmodel_T1_mdl = tf.keras.models.load_model( mdlfn, compile=False )
            else:
                print( mdlfn + " does not exist - will not run.")
            hierSR = antspyt1w.hierarchical_to_sr( hier, srmodel_T1_mdl, blending=None, tissue_sr=False )
            antspyt1w.write_hierarchical( hierSR, hierfnSR )
            t1wideSR = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                    hierSR['dataframes'], identifier=None )
            t1wideSR.to_csv( hierfnSR + 'mmwide.csv' )
    hier = antspyt1w.read_hierarchical( hierfn )
    if exists( hierfn + 'mmwide.csv' ) :
        t1wide = pd.read_csv( hierfn + 'mmwide.csv' )
    elif not testloop:
        t1wide = antspyt1w.merge_hierarchical_csvs_to_wide_format(
                hier['dataframes'], identifier=None )
    if not testloop:
        t1imgbrn = hier['brain_n4_dnz']
        t1atropos = hier['dkt_parc']['tissue_segmentation']

    if not exists( regout + "logjacobian.nii.gz" ) or not exists( regout+'1Warp.nii.gz' ):
        if verbose:
            print('start t1 registration')
        ex_path = os.path.expanduser( "~/.antspyt1w/" )
        templatefn = ex_path + 'CIT168_T1w_700um_pad_adni.nii.gz'
        template = mm_read( templatefn )
        template = ants.resample_image( template, [1,1,1], use_voxels=False )
        t1reg = ants.registration( template, 
            hier['brain_n4_dnz'],
            "antsRegistrationSyNQuickRepro[s]", outprefix = regout, verbose=False )
        myjac = ants.create_jacobian_determinant_image( template,
            t1reg['fwdtransforms'][0], do_log=True, geom=True )
        image_write_with_thumbnail( myjac, regout + "logjacobian.nii.gz", thumb=False )
        if visualize:
            ants.plot( ants.iMath(t1reg['warpedmovout'],"Normalize"),  axis=2, nslices=21, ncol=7, crop=True, title='warped to template', filename=regout+"totemplate.png" )
            ants.plot( ants.iMath(myjac,"Normalize"),  axis=2, nslices=21, ncol=7, crop=True, title='jacobian', filename=regout+"jacobian.png" )

    if normalization_template_output is not None and normalization_template is not None:
        if verbose:
            print("begin group template registration")
        if not exists( normout+'0GenericAffine.mat' ):
            if normalization_template_spacing is not None:
                normalization_template_rr=ants.resample_image(normalization_template,normalization_template_spacing)
            else:
                normalization_template_rr=normalization_template
            greg = ants.registration( 
                normalization_template_rr, 
                hier['brain_n4_dnz'],
                normalization_template_transform_type,
                outprefix = normout, verbose=False )
            myjac = ants.create_jacobian_determinant_image( template,
                    greg['fwdtransforms'][0], do_log=True, geom=True )
            image_write_with_thumbnail( myjac, normout + "logjacobian.nii.gz", thumb=False )
            if verbose:
                print("end group template registration")
        else:
            if verbose:
                print("group template registration already done")

    # loop over modalities and then unique image IDs
    # we treat NM in a "special" way -- aggregating repeats
    # other modalities (beyond T1) are treated individually
    for overmodX in nrg_modality_list:
        # define 1. input images 2. output prefix
        mydoc = docsamson( overmodX, studycsv=studycsv, outputdir=outputdir, projid=projid, sid=sid, dtid=dtid, mysep=mysep,t1iid=t1iidUse )
        myimgsr = mydoc['images']
        mymm = mydoc['outprefix']
        mymod = mydoc['modality']
        if verbose:
            print( mydoc )
        if len(myimgsr) > 0:
            dowrite=False
            if verbose:
                print( 'overmodX is : ' + overmodX )
                print( 'example image name is : '  )
                print( myimgsr )
            if overmodX == 'NM2DMT':
                dowrite = True
                visualize = True
                subjectpropath = os.path.dirname( mydoc['outprefix'] )
                if verbose:
                    print("subjectpropath is")
                    print(subjectpropath)
                    os.makedirs( subjectpropath, exist_ok=True  )
                myimgsr2 = myimgsr
                myimgsr2.sort()
                is4d = False
                temp = ants.image_read( myimgsr2[0] )
                if temp.dimension == 4:
                    is4d = True
                if len( myimgsr2 ) == 1 and not is4d: # check dimension
                    myimgsr2 = myimgsr2 + myimgsr2
                mymmout = makewideout( mymm )
                if verbose and not exists( mymmout ):
                    print( "NM " + mymm  + ' execution ')
                elif verbose and exists( mymmout ) :
                    print( "NM " + mymm + ' complete ' )
                if exists( mymmout ):
                    continue
                if is4d:
                    nmlist = ants.ndimage_to_list( mm_read( myimgsr2[0] ) )
                else:
                    nmlist = []
                    for zz in myimgsr2:
                        nmlist.append( mm_read( zz ) )
                srmodel_NM_mdl = None
                if srmodel_NM is not None:
                    bestup = siq.optimize_upsampling_shape( ants.get_spacing(nmlist[0]), modality='NM', roundit=True )
                    mdlfn = ex_pathmm + "siq_default_sisr_" + bestup + "_1chan_featvggL6_best_mdl.keras"
                    if isinstance( srmodel_NM, str ):
                        srmodel_NM = re.sub( "bestup", bestup, srmodel_NM )
                        mdlfn = os.path.join( ex_pathmm, srmodel_NM )
                    if exists( mdlfn ):
                        if verbose:
                            print(mdlfn)
                        srmodel_NM_mdl = tf.keras.models.load_model( mdlfn, compile=False  )
                    else:
                        print( mdlfn + " does not exist - wont use SR")
                if not testloop:
                    try:
                        tabPro, normPro = mm( t1, hier,
                            nm_image_list = nmlist,
                            srmodel=srmodel_NM_mdl,
                            do_tractography=False,
                            do_kk=False,
                            do_normalization=templateTx,
                            group_template = normalization_template,
                            group_transform = groupTx,
                            test_run=test_run,
                            verbose=True )
                    except Exception as e:
                        error_info = traceback.format_exc()
                        print(error_info)
                        visualize=False
                        dowrite=False
                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                        pass
                    if not test_run:
                        if dowrite:
                            write_mm( output_prefix=mymm, mm=tabPro,
                                mm_norm=normPro, t1wide=None, separator=mysep )
                        if visualize :
                            nmpro = tabPro['NM']
                            mysl = range( nmpro['NM_avg'].shape[2] )
                            ants.plot( nmpro['NM_avg'],  nmpro['t1_to_NM'], slices=mysl, axis=2, title='nm + t1', filename=mymm+mysep+"NMavg.png" )
                            mysl = range( nmpro['NM_avg_cropped'].shape[2] )
                            ants.plot( nmpro['NM_avg_cropped'], axis=2, slices=mysl, overlay_alpha=0.3, title='nm crop', filename=mymm+mysep+"NMavgcrop.png" )
                            ants.plot( nmpro['NM_avg_cropped'], nmpro['t1_to_NM'], axis=2, slices=mysl, overlay_alpha=0.3, title='nm crop + t1', filename=mymm+mysep+"NMavgcropt1.png" )
                            ants.plot( nmpro['NM_avg_cropped'], nmpro['NM_labels'], axis=2, slices=mysl, title='nm crop + labels', filename=mymm+mysep+"NMavgcroplabels.png" )
            else :
                if len( myimgsr ) > 0 :
                    dowrite=False
                    myimgcount=0
                    if len( myimgsr ) > 0 :
                        myimg = myimgsr[ myimgcount ]
                        subjectpropath = os.path.dirname( mydoc['outprefix'] )
                        if verbose:
                            print("subjectpropath is")
                            print(subjectpropath)
                        os.makedirs( subjectpropath, exist_ok=True  )
                        mymmout = makewideout( mymm )
                        if verbose and not exists( mymmout ):
                            print( "Modality specific processing: " + mymod + " execution " )
                            print( mymm )
                        elif verbose and exists( mymmout ) :
                            print("Modality specific processing: " + mymod + " complete " )
                        if exists( mymmout ) :
                            continue
                        if verbose:
                            print( subjectpropath )
                            print( myimg )
                        if not testloop:
                            img = mm_read( myimg )
                            ishapelen = len( img.shape )
                            if mymod == 'T1w' and ishapelen == 3:
                                if not exists( mymm + mysep + "kk_norm.nii.gz" ):
                                    dowrite=True
                                    if verbose:
                                        print('start kk')
                                    try:
                                        tabPro, normPro = mm( t1, hier,
                                            srmodel=None,
                                            do_tractography=False,
                                            do_kk=True,
                                            do_normalization=templateTx,
                                            group_template = normalization_template,
                                            group_transform = groupTx,
                                            test_run=test_run,
                                            verbose=True )
                                    except Exception as e:
                                        error_info = traceback.format_exc()
                                        print(error_info)
                                        visualize=False
                                        dowrite=False
                                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                        pass
                                    if visualize:
                                        maxslice = np.min( [21, hier['brain_n4_dnz'].shape[2] ] )
                                        ants.plot( hier['brain_n4_dnz'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='brain extraction', filename=mymm+mysep+"brainextraction.png" )
                                        ants.plot( tabPro['kk']['thickness_image'], axis=2, nslices=maxslice, ncol=7, crop=True, title='kk',
                                        cmap='plasma', filename=mymm+mysep+"kkthickness.png" )
                            if mymod == 'T2Flair' and ishapelen == 3 and np.min(img.shape) > 15:
                                dowrite=True
                                try:
                                    tabPro, normPro = mm( t1, hier,
                                        flair_image = img,
                                        srmodel=None,
                                        do_tractography=False,
                                        do_kk=False,
                                        do_normalization=templateTx,
                                        group_template = normalization_template,
                                        group_transform = groupTx,
                                        test_run=test_run,
                                        verbose=True )
                                except Exception as e:
                                        error_info = traceback.format_exc()
                                        print(error_info)
                                        visualize=False
                                        dowrite=False
                                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                        pass
                                if visualize:
                                    maxslice = np.min( [21, img.shape[2] ] )
                                    ants.plot_ortho( img, crop=True, title='Flair', filename=mymm+mysep+"flair.png", flat=True )
                                    ants.plot_ortho( img, tabPro['flair']['WMH_probability_map'], crop=True, title='Flair + WMH', filename=mymm+mysep+"flairWMH.png", flat=True )
                                    if tabPro['flair']['WMH_posterior_probability_map'] is not None:
                                        ants.plot_ortho( img, tabPro['flair']['WMH_posterior_probability_map'],  crop=True, title='Flair + prior WMH', filename=mymm+mysep+"flairpriorWMH.png", flat=True )
                            if ( mymod == 'rsfMRI_LR' or mymod == 'rsfMRI_RL' or mymod == 'rsfMRI' )  and ishapelen == 4:
                                img2 = None
                                if len( myimgsr ) > 1:
                                    img2 = mm_read( myimgsr[myimgcount+1] )
                                    ishapelen2 = len( img2.shape )
                                    if ishapelen2 != 4 or 1 in img2.shape:
                                        img2 = None
                                if 1 in img.shape:
                                    warnings.warn( 'rsfMRI image shape suggests it is an incorrectly converted mosaic image - will not process.')
                                    dowrite=False
                                    tabPro={'rsf':None}
                                    normPro={'rsf':None}
                                else:
                                    dowrite=True
                                    try:
                                        tabPro, normPro = mm( t1, hier,
                                            rsf_image=[img,img2],
                                            srmodel=None,
                                            do_tractography=False,
                                            do_kk=False,
                                            do_normalization=templateTx,
                                            group_template = normalization_template,
                                            group_transform = groupTx,
                                            rsf_upsampling = rsf_upsampling,
                                            test_run=test_run,
                                            verbose=True )
                                    except Exception as e:
                                        error_info = traceback.format_exc()
                                        print(error_info)
                                        visualize=False
                                        dowrite=False
                                        tabPro={'rsf':None}
                                        normPro={'rsf':None}
                                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                        pass
                                if tabPro['rsf'] is not None and visualize:
                                    for tpro in tabPro['rsf']: # FIXMERSF
                                        maxslice = np.min( [21, tpro['meanBold'].shape[2] ] )
                                        tproprefix = mymm+mysep+str(tpro['paramset'])+mysep
                                        ants.plot( tpro['meanBold'],
                                            axis=2, nslices=maxslice, ncol=7, crop=True, title='meanBOLD', filename=tproprefix+"meanBOLD.png" )
                                        ants.plot( tpro['meanBold'], ants.iMath(tpro['alff'],"Normalize"),
                                            axis=2, nslices=maxslice, ncol=7, crop=True, title='ALFF', filename=tproprefix+"boldALFF.png" )
                                        ants.plot( tpro['meanBold'], ants.iMath(tpro['falff'],"Normalize"),
                                            axis=2, nslices=maxslice, ncol=7, crop=True, title='fALFF', filename=tproprefix+"boldfALFF.png" )
                                        dfn=tpro['dfnname']
                                        ants.plot( tpro['meanBold'], tpro[dfn],
                                            axis=2, nslices=maxslice, ncol=7, crop=True, title=dfn, filename=tproprefix+"boldDefaultMode.png" )
                            if ( mymod == 'perf' ) and ishapelen == 4:
                                dowrite=True
                                try:
                                    tabPro, normPro = mm( t1, hier,
                                        perfusion_image=img,
                                        srmodel=None,
                                        do_tractography=False,
                                        do_kk=False,
                                        do_normalization=templateTx,
                                        group_template = normalization_template,
                                        group_transform = groupTx,
                                        test_run=test_run,
                                        perfusion_trim=perfusion_trim,
                                        perfusion_m0_image=perfusion_m0_image,
                                        perfusion_m0=perfusion_m0,
                                        verbose=True )
                                except Exception as e:
                                        error_info = traceback.format_exc()
                                        print(error_info)
                                        visualize=False
                                        dowrite=False
                                        tabPro={'perf':None}
                                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                        pass
                                if tabPro['perf'] is not None and visualize:
                                    maxslice = np.min( [21, tabPro['perf']['meanBold'].shape[2] ] )
                                    ants.plot( tabPro['perf']['perfusion'],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='perfusion image', filename=mymm+mysep+"perfusion.png" )
                                    ants.plot( tabPro['perf']['cbf'],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='CBF image', filename=mymm+mysep+"cbf.png" )
                                    ants.plot( tabPro['perf']['m0'],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='M0 image', filename=mymm+mysep+"m0.png" )

                            if ( mymod == 'pet3d' ) and ishapelen == 3:
                                dowrite=True
                                try:
                                    tabPro, normPro = mm( t1, hier,
                                        srmodel=None,
                                        do_tractography=False,
                                        do_kk=False,
                                        do_normalization=templateTx,
                                        group_template = normalization_template,
                                        group_transform = groupTx,
                                        test_run=test_run,
                                        pet_3d_image=img,
                                        verbose=True )
                                except Exception as e:
                                        error_info = traceback.format_exc()
                                        print(error_info)
                                        visualize=False
                                        dowrite=False
                                        tabPro={'pet3d':None}
                                        print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                        pass
                                if tabPro['pet3d'] is not None and visualize:
                                    maxslice = np.min( [21, tabPro['pet3d']['pet3d'].shape[2] ] )
                                    ants.plot( tabPro['pet3d']['pet3d'],
                                        axis=2, nslices=maxslice, ncol=7, crop=True, title='PET image', filename=mymm+mysep+"pet3d.png" )
                            if ( mymod == 'DTI_LR' or mymod == 'DTI_RL' or mymod == 'DTI' ) and ishapelen == 4:
                                bvalfn = re.sub( '.nii.gz', '.bval' , myimg )
                                bvecfn = re.sub( '.nii.gz', '.bvec' , myimg )
                                imgList = [ img ]
                                bvalfnList = [ bvalfn ]
                                bvecfnList = [ bvecfn ]
                                missing_dti_data=False # bval, bvec or images
                                if len( myimgsr ) == 2:  # find DTI_RL
                                    dtilrfn = myimgsr[myimgcount+1]
                                    if exists( dtilrfn ):
                                        bvalfnRL = re.sub( '.nii.gz', '.bval' , dtilrfn )
                                        bvecfnRL = re.sub( '.nii.gz', '.bvec' , dtilrfn )
                                        imgRL = ants.image_read( dtilrfn )
                                        imgList.append( imgRL )
                                        bvalfnList.append( bvalfnRL )
                                        bvecfnList.append( bvecfnRL )
                                elif len( myimgsr ) == 3:  # find DTI_RL
                                    print("DTI trinity")
                                    dtilrfn = myimgsr[myimgcount+1]
                                    dtilrfn2 = myimgsr[myimgcount+2]
                                    if exists( dtilrfn ) and exists( dtilrfn2 ):
                                        bvalfnRL = re.sub( '.nii.gz', '.bval' , dtilrfn )
                                        bvecfnRL = re.sub( '.nii.gz', '.bvec' , dtilrfn )
                                        bvalfnRL2 = re.sub( '.nii.gz', '.bval' , dtilrfn2 )
                                        bvecfnRL2 = re.sub( '.nii.gz', '.bvec' , dtilrfn2 )
                                        imgRL = ants.image_read( dtilrfn )
                                        imgRL2 = ants.image_read( dtilrfn2 )
                                        bvals, bvecs = read_bvals_bvecs( bvalfnRL , bvecfnRL  )
                                        print( bvals.max() )
                                        bvals2, bvecs2 = read_bvals_bvecs( bvalfnRL2 , bvecfnRL2  )
                                        print( bvals2.max() )
                                        temp = merge_dwi_data( imgRL, bvals, bvecs, imgRL2, bvals2, bvecs2  )
                                        imgList.append( temp[0] )
                                        bvalfnList.append( mymm+mysep+'joined.bval' )
                                        bvecfnList.append( mymm+mysep+'joined.bvec' )
                                        write_bvals_bvecs( temp[1], temp[2], mymm+mysep+'joined' )
                                        bvalsX, bvecsX = read_bvals_bvecs( bvalfnRL2 , bvecfnRL2  )
                                        print( bvalsX.max() )
                                # check existence of all files expected ...
                                for dtiex in bvalfnList+bvecfnList+myimgsr:
                                    if not exists(dtiex):
                                        print('mm_csv: missing dti data ' + dtiex )
                                        missing_dti_data=True
                                        dowrite=False
                                if not missing_dti_data:
                                    dowrite=True
                                    srmodel_DTI_mdl=None
                                    if srmodel_DTI is not None:
                                        temp = ants.get_spacing(img)
                                        dtspc=[temp[0],temp[1],temp[2]]
                                        bestup = siq.optimize_upsampling_shape( dtspc, modality='DTI' )
                                        mdlfn = re.sub( 'bestup', bestup, srmodel_DTI )
                                        if isinstance( srmodel_DTI, str ):
                                            srmodel_DTI = re.sub( "bestup", bestup, srmodel_DTI )
                                            mdlfn = os.path.join( ex_pathmm, srmodel_DTI )
                                        if exists( mdlfn ):
                                            if verbose:
                                                print(mdlfn)
                                            srmodel_DTI_mdl = tf.keras.models.load_model( mdlfn, compile=False )
                                        else:
                                            print(mdlfn + " does not exist - wont use SR")
                                    try:
                                        tabPro, normPro = mm( t1, hier,
                                            dw_image=imgList,
                                            bvals = bvalfnList,
                                            bvecs = bvecfnList,
                                            srmodel=srmodel_DTI_mdl,
                                            do_tractography=not test_run,
                                            do_kk=False,
                                            do_normalization=templateTx,
                                            group_template = normalization_template,
                                            group_transform = groupTx,
                                            dti_motion_correct = dti_motion_correct,
                                            dti_denoise = dti_denoise,
                                            test_run=test_run,
                                            verbose=True )
                                    except Exception as e:
                                            error_info = traceback.format_exc()
                                            print(error_info)
                                            visualize=False
                                            dowrite=False
                                            tabPro={'DTI':None}
                                            print(f"antspymmerror occurred while processing {overmodX}: {e}")
                                            pass
                                    mydti = tabPro['DTI']
                                    if visualize and tabPro['DTI'] is not None:
                                        maxslice = np.min( [21, mydti['recon_fa'] ] )
                                        ants.plot( mydti['recon_fa'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='FA', filename=mymm+mysep+"FAbetter.png"  )
                                        ants.plot( mydti['recon_fa'], mydti['jhu_labels'], axis=2, nslices=maxslice, ncol=7, crop=True, title='FA + JHU', filename=mymm+mysep+"FAJHU.png"  )
                                        ants.plot( mydti['recon_md'],  axis=2, nslices=maxslice, ncol=7, crop=True, title='MD', filename=mymm+mysep+"MD.png"  )
                            if dowrite:
                                write_mm( output_prefix=mymm, mm=tabPro, mm_norm=normPro, t1wide=t1wide, separator=mysep )
                                for mykey in normPro.keys():
                                    if normPro[mykey] is not None and normPro[mykey].components == 1:
                                        if visualize and False:
                                            ants.plot( template, normPro[mykey], axis=2, nslices=21, ncol=7, crop=True, title=mykey, filename=mymm+mysep+mykey+".png"   )
        if overmodX == nrg_modality_list[ len( nrg_modality_list ) - 1 ]:
            return
        if verbose:
            print("done with " + overmodX )
    if verbose:
        print("mm_nrg complete.")
    return

