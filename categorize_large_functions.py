#!/usr/bin/env python
"""
Categorize large functions for extraction into logical modules
"""

# Large functions categorized by functionality
function_categories = {
    'registration': [
        'dti_reg',
        'timeseries_reg', 
        'mc_reg',
        'transform_and_reorient_dti',
        'apply_transforms_mixed_interpolation'
    ],
    
    'dti_processing': [
        'dipy_dti_recon',
        'joint_dti_recon',
        'dwi_deterministic_tracking',
        'dwi_closest_peak_tracking',
        'dwi_streamline_connectivity',
        'dwi_streamline_connectivity_old',
        'dwi_streamline_pairwise_connectivity_old',
        'efficient_dwi_fit',
        'efficient_dwi_fit_voxelwise',
        'efficient_tensor_fit',
        'fix_dwi_shape',
        'get_average_dwi_b0',
        'dti_template',
        't1_based_dwi_brain_extraction',
        'concat_dewarp'
    ],
    
    'image_processing': [
        'neuromelanin',
        'wmh',
        'dewarp_imageset',
        'super_res_mcimage',
        't1w_super_resolution_with_hemispheres',
        'tra_initializer',
        'bold_perfusion',
        'bold_perfusion_minimal',
        'template_figure_with_overlay'
    ],
    
    'fmri_processing': [
        'resting_state_fmri_networks',
        'impute_timeseries',
        'score_fmri_censoring'
    ],
    
    'data_analysis': [
        'mean_of_list',
        'one_hot_encode',  # appears twice in list
        'blind_image_assessment',
        'quick_viz_mm_nrg',
        'rob',
        'pet3d_summary',
        'calculate_loop_scores',
        'get_biggest_part'
    ],
    
    'data_management': [
        'makewideout',  # appears twice in list - probably duplicate functions
        'study_dataframe_from_matched_dataframe',
        'merge_wides_to_study_dataframe',
        'myread_csv',  # appears twice in list
        'match_modalities',
        'outlierness_by_modality',
        'bind_wide_mm_csvs',
        'read_mm_csv',
        'filter_image_files',
        'highest_quality_repeat'
    ],
    
    'qc_matching': [
        'mm_match_by_qc_scoring',
        'mm_match_by_qc_scoring_all',
        'fix_LR_RL_stuff',
        'check_pd_construction',  # appears twice in list
        'shorten_pymm_names',
        'shorten_pymm_names2'
    ],
    
    'signal_processing': [
        'daniell_window_convolve',
        'conv_circular'
    ],
    
    'utilities': [
        'is_bst_region',
        'docsamson',
        'best_mmm',
        'get_hemisphere_and_base',
        'map_idps_to_rois'
    ],
    
    # Keep these in mm.py as they are core pipeline functions
    'core_pipeline': [
        'mm',        # 477 lines - main pipeline
        'mm_csv',    # 127 lines - CSV pipeline  
        'mm_nrg'     # 85 lines - NRG pipeline
    ]
}

def analyze_categories():
    """Analyze the categorization and extraction potential"""
    
    # Function sizes from previous analysis
    function_sizes = {
        'makewideout': [567, 419],  # Two functions with same name
        'mm': 477,
        'mean_of_list': 404,
        'is_bst_region': 336,
        'one_hot_encode': [291, 167],  # Two functions with same name
        'quick_viz_mm_nrg': 280,
        'blind_image_assessment': 279,
        'dti_reg': 249,
        'neuromelanin': 198,
        'fix_dwi_shape': 190,
        'myread_csv': [185, 109],  # Two functions with same name
        'timeseries_reg': 180,
        'rob': 166,
        'dwi_deterministic_tracking': 161,
        'mc_reg': 153,
        'match_modalities': 150,
        'study_dataframe_from_matched_dataframe': 142,
        'dwi_streamline_connectivity_old': 141,
        'check_pd_construction': [134, 72],  # Two functions with same name
        'dwi_closest_peak_tracking': 134,
        'mm_match_by_qc_scoring_all': 131,
        'mm_csv': 127,
        'transform_and_reorient_dti': 120,
        'dipy_dti_recon': 119,
        'get_hemisphere_and_base': 117,
        'wmh': 112,
        'pet3d_summary': 109,
        'resting_state_fmri_networks': 108,
        'dewarp_imageset': 105,
        'merge_wides_to_study_dataframe': 104,
        'docsamson': 103,
        'get_biggest_part': 103,
        'calculate_loop_scores': 100,
        'template_figure_with_overlay': 97,
        'bold_perfusion': 96,
        't1w_super_resolution_with_hemispheres': 96,
        'joint_dti_recon': 94,
        'tra_initializer': 85,
        'mm_nrg': 85,
        'super_res_mcimage': 83,
        'map_idps_to_rois': 79,
        'apply_transforms_mixed_interpolation': 77,
        'dti_template': 75,
        'daniell_window_convolve': 74,
        'best_mmm': 72,
        'efficient_dwi_fit': 72,
        'shorten_pymm_names2': 69,
        'mm_match_by_qc_scoring': 69,
        'dwi_streamline_connectivity': 68,
        'conv_circular': 68,
        'score_fmri_censoring': 67,
        'impute_timeseries': 61,
        't1_based_dwi_brain_extraction': 60,
        'filter_image_files': 59,
        'shorten_pymm_names': 58,
        'outlierness_by_modality': 57,
        'bind_wide_mm_csvs': 57,
        'efficient_dwi_fit_voxelwise': 56,
        'read_mm_csv': 56,
        'fix_LR_RL_stuff': 56,
        'highest_quality_repeat': 55,
        'get_average_dwi_b0': 55,
        'dwi_streamline_pairwise_connectivity_old': 55,
        'efficient_tensor_fit': 53,
        'concat_dewarp': 51,
        'bold_perfusion_minimal': 49
    }
    
    def get_size(func_name):
        size = function_sizes.get(func_name, 0)
        if isinstance(size, list):
            return sum(size)
        return size
    
    print("Function Categories for Extraction:")
    print("=" * 60)
    
    total_extractable = 0
    keep_in_mm = 0
    
    for category, functions in function_categories.items():
        category_size = sum(get_size(func) for func in functions)
        
        if category == 'core_pipeline':
            keep_in_mm += category_size
            print(f"\n{category.upper()} (KEEP IN mm.py): {category_size} lines")
        else:
            total_extractable += category_size
            print(f"\n{category.upper()}: {category_size} lines")
        
        for func in functions:
            size = get_size(func)
            if size > 0:
                print(f"  - {func}: {size} lines")
    
    print("\n" + "=" * 60)
    print(f"Total extractable lines: {total_extractable}")
    print(f"Core pipeline lines to keep: {keep_in_mm}")
    print(f"Current mm.py size: 11,890 lines")
    print(f"Estimated new size: {11890 - total_extractable} lines")
    print(f"Reduction: {(total_extractable/11890)*100:.1f}%")

if __name__ == '__main__':
    analyze_categories()