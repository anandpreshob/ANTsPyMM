#!/usr/bin/env python
"""
Extract large functions from mm.py to achieve significant size reduction
"""

import re
import shutil

# Functions to extract by category
functions_to_extract = {
    'data_management': [
        'study_dataframe_from_matched_dataframe',
        'merge_wides_to_study_dataframe', 
        'myread_csv',
        'match_modalities',
        'outlierness_by_modality',
        'bind_wide_mm_csvs',
        'read_mm_csv',
        'filter_image_files',
        'highest_quality_repeat'
    ],
    
    'data_analysis': [
        'mean_of_list',
        'one_hot_encode',
        'blind_image_assessment',
        'quick_viz_mm_nrg',
        'rob',
        'pet3d_summary',
        'calculate_loop_scores',
        'get_biggest_part'
    ],
    
    'registration': [
        'dti_reg',
        'timeseries_reg',
        'mc_reg', 
        'transform_and_reorient_dti',
        'apply_transforms_mixed_interpolation'
    ],
    
    'dti_advanced': [
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
    
    'image_advanced': [
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
    
    'fmri': [
        'resting_state_fmri_networks',
        'impute_timeseries',
        'score_fmri_censoring'
    ],
    
    'qc_advanced': [
        'mm_match_by_qc_scoring',
        'mm_match_by_qc_scoring_all',
        'fix_LR_RL_stuff',
        'check_pd_construction',
        'shorten_pymm_names',
        'shorten_pymm_names2'
    ],
    
    'signal_processing': [
        'daniell_window_convolve',
        'conv_circular'
    ],
    
    'misc_utils': [
        'is_bst_region',
        'docsamson',
        'best_mmm',
        'get_hemisphere_and_base',
        'map_idps_to_rois'
    ]
}

def find_function_bounds(lines, func_name):
    """Find the exact start and end lines of a function definition"""
    start_line = None
    
    # Find function start
    for i, line in enumerate(lines):
        if re.match(rf'^def\s+{re.escape(func_name)}\s*\(', line.strip()):
            start_line = i
            break
    
    if start_line is None:
        return None, None
    
    # Find function end by looking for next function definition or same-level code
    def_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
    
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        # If we find a line at the same or lesser indentation, this is likely the end
        if current_indent <= def_indent:
            # Double check it's not just a continuing part of our function
            if (line.strip().startswith('def ') or 
                line.strip().startswith('class ') or
                line.strip().startswith('import ') or
                line.strip().startswith('from ') or
                re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line.strip()) or  # Constants
                line.strip().startswith('__all__')):
                return start_line, i - 1
    
    # If we reach the end of file
    return start_line, len(lines) - 1

def extract_functions_by_category(category, functions):
    """Extract functions for a specific category"""
    
    print(f"\nExtracting {category.upper()} functions...")
    
    # Create module directory
    module_dir = f'antspymm/{category}'
    import os
    os.makedirs(module_dir, exist_ok=True)
    
    # Read mm.py
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    # Find and extract functions
    extracted_functions = []
    functions_found = []
    
    for func_name in functions:
        start, end = find_function_bounds(lines, func_name)
        if start is not None:
            func_lines = lines[start:end+1]
            extracted_functions.append((func_name, func_lines))
            functions_found.append((func_name, start, end))
            print(f"  Found {func_name}: lines {start+1}-{end+1} ({end-start+1} lines)")
        else:
            print(f"  WARNING: {func_name} not found")
    
    if extracted_functions:
        # Create module file
        module_file = f'{module_dir}/{category}.py'
        with open(module_file, 'w') as f:
            f.write(f'"""\n{category.title()} functions for ANTsPyMM\n')
            f.write('Extracted from mm.py - maintains exact original functionality\n"""\n\n')
            f.write('# Standard library imports\n')
            f.write('import os\nimport numpy as np\nimport pandas as pd\n\n')
            f.write('# Conditional imports\n')
            f.write('try:\n    import ants\nexcept ImportError:\n    ants = None\n\n')
            
            # Write each function
            for func_name, func_lines in extracted_functions:
                f.write(f'# {func_name}\n')
                f.writelines(func_lines)
                f.write('\n\n')
        
        # Create __init__.py
        init_file = f'{module_dir}/__init__.py'
        with open(init_file, 'w') as f:
            f.write(f'"""\n{category.title()} module for ANTsPyMM\n"""\n\n')
            f.write(f'from .{category} import (\n')
            for func_name, _ in extracted_functions:
                f.write(f'    {func_name},\n')
            f.write(')\n\n')
            f.write('__all__ = [\n')
            for func_name, _ in extracted_functions:
                f.write(f"    '{func_name}',\n")
            f.write(']\n')
        
        print(f"  Created {module_file} with {len(extracted_functions)} functions")
        return functions_found
    else:
        print(f"  No functions found for {category}")
        return []

def main():
    """Extract large functions to reduce mm.py size"""
    
    # Create backup
    shutil.copy2('antspymm/mm.py', 'antspymm/mm.py.before_large_extraction')
    print("Created backup: antspymm/mm.py.before_large_extraction")
    
    # Track original size
    with open('antspymm/mm.py', 'r') as f:
        original_lines = len(f.readlines())
    print(f"Original mm.py size: {original_lines} lines")
    
    # Extract functions by category (start with smaller categories first)
    categories_to_extract = [
        'signal_processing',
        'fmri', 
        'misc_utils',
        'qc_advanced',
        'registration'
    ]
    
    all_extracted = []
    for category in categories_to_extract:
        if category in functions_to_extract:
            functions = functions_to_extract[category]
            extracted = extract_functions_by_category(category, functions)
            all_extracted.extend(extracted)
    
    # Show summary
    total_functions = len(all_extracted)
    total_lines = sum(end - start + 1 for _, start, end in all_extracted)
    
    print(f"\n" + "="*60)
    print(f"EXTRACTION SUMMARY")
    print(f"="*60)
    print(f"Functions extracted: {total_functions}")
    print(f"Lines that will be removed: {total_lines}")
    print(f"Original size: {original_lines} lines")
    print(f"Estimated new size: {original_lines - total_lines} lines")
    print(f"Estimated reduction: {(total_lines/original_lines)*100:.1f}%")
    
    return all_extracted

if __name__ == '__main__':
    extracted = main()