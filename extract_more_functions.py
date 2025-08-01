#!/usr/bin/env python
"""
Extract more large functions from mm.py - data management and analysis
"""

import os
import re
import shutil

# Additional functions to extract
more_functions_to_extract = {
    'data_management': [
        'study_dataframe_from_matched_dataframe',
        'merge_wides_to_study_dataframe', 
        'match_modalities',
        'outlierness_by_modality',
        'bind_wide_mm_csvs',
        'read_mm_csv',
        'filter_image_files',
        'highest_quality_repeat',
        'myread_csv'  # Two functions with this name
    ],
    
    'data_analysis': [
        'mean_of_list',
        'one_hot_encode',  # Two functions with this name
        'blind_image_assessment',  
        'quick_viz_mm_nrg',
        'rob',
        'pet3d_summary',
        'calculate_loop_scores',
        'get_biggest_part'
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
    ]
}

def find_all_function_occurrences(lines, func_name):
    """Find ALL occurrences of a function name (since some appear multiple times)"""
    occurrences = []
    
    # Find all function starts
    for i, line in enumerate(lines):
        if re.match(rf'^def\s+{re.escape(func_name)}\s*\(', line.strip()):
            # Find end of this function
            def_indent = len(lines[i]) - len(lines[i].lstrip())
            
            for j in range(i + 1, len(lines)):
                line_j = lines[j]
                
                # Skip empty lines and comments
                if not line_j.strip() or line_j.strip().startswith('#'):
                    continue
                    
                current_indent = len(line_j) - len(line_j.lstrip())
                
                # If we find a line at the same or lesser indentation, this is likely the end  
                if current_indent <= def_indent:
                    if (line_j.strip().startswith('def ') or 
                        line_j.strip().startswith('class ') or
                        line_j.strip().startswith('import ') or
                        line_j.strip().startswith('from ') or
                        re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line_j.strip()) or
                        line_j.strip().startswith('__all__')):
                        occurrences.append((i, j - 1))
                        break
            else:
                # Reached end of file
                occurrences.append((i, len(lines) - 1))
    
    return occurrences

def extract_functions_aggressively():
    """Extract more functions to achieve bigger reduction"""
    
    # Read mm.py
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    original_size = len(lines)
    print(f"Current mm.py size: {original_size} lines")
    
    all_functions_to_remove = []
    
    # Process each category
    for category, functions in more_functions_to_extract.items():
        print(f"\nAnalyzing {category.upper()} functions...")
        
        category_functions = []
        
        for func_name in functions:
            occurrences = find_all_function_occurrences(lines, func_name)
            
            if occurrences:
                for idx, (start, end) in enumerate(occurrences):
                    suffix = f"_{idx+1}" if len(occurrences) > 1 else ""
                    name_with_suffix = f"{func_name}{suffix}"
                    size = end - start + 1
                    
                    category_functions.append((name_with_suffix, func_name, start, end, size))
                    print(f"  Found {name_with_suffix}: lines {start+1}-{end+1} ({size} lines)")
            else:
                print(f"  WARNING: {func_name} not found")
        
        all_functions_to_remove.extend(category_functions)
    
    # Calculate total reduction
    total_lines_to_remove = sum(f[4] for f in all_functions_to_remove)
    estimated_new_size = original_size - total_lines_to_remove
    
    print(f"\n" + "="*60)
    print(f"AGGRESSIVE EXTRACTION PLAN")
    print(f"="*60)
    print(f"Functions to extract: {len(all_functions_to_remove)}")
    print(f"Lines to remove: {total_lines_to_remove}")
    print(f"Current size: {original_size} lines")
    print(f"Estimated new size: {estimated_new_size} lines")
    print(f"Estimated reduction: {(total_lines_to_remove/original_size)*100:.1f}%")
    
    return all_functions_to_remove

def remove_functions(functions_to_remove):
    """Remove the identified functions from mm.py"""
    
    # Read the file
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    original_line_count = len(lines)
    
    # Sort by start line in reverse order so we can remove from bottom up
    functions_to_remove.sort(key=lambda x: x[2], reverse=True)
    
    # Remove functions from bottom to top to preserve line numbers
    lines_removed = 0
    for name_with_suffix, original_name, start, end, size in functions_to_remove:
        print(f"Removing {name_with_suffix} (lines {start+1}-{end+1})")
        del lines[start:end+1]
        lines_removed += size
    
    # Write the modified file
    with open('antspymm/mm.py', 'w') as f:
        f.writelines(lines)
    
    new_line_count = len(lines)
    print(f"\nRemoval Summary:")
    print(f"Original size: {original_line_count} lines")
    print(f"New size: {new_line_count} lines") 
    print(f"Removed: {lines_removed} lines")
    print(f"Reduction: {(lines_removed/original_line_count)*100:.1f}%")
    print(f"Functions removed: {len(functions_to_remove)}")

if __name__ == '__main__':
    # Create another backup
    shutil.copy2('antspymm/mm.py', 'antspymm/mm.py.before_aggressive_extraction')
    print("Created backup: antspymm/mm.py.before_aggressive_extraction")
    
    # Analyze what can be extracted
    functions_to_remove = extract_functions_aggressively()
    
    # Ask for confirmation before removing
    response = input(f"\nProceed with removing {len(functions_to_remove)} functions? (y/n): ")
    if response.lower() == 'y':
        remove_functions(functions_to_remove)
    else:
        print("Extraction cancelled")