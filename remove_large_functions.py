#!/usr/bin/env python
"""
Remove the extracted large functions from mm.py
"""

import re

# Functions that were extracted (from the previous extraction)
extracted_functions = [
    # signal_processing
    'daniell_window_convolve',
    'conv_circular',
    
    # fmri
    'resting_state_fmri_networks',
    'impute_timeseries', 
    'score_fmri_censoring',
    
    # misc_utils
    'is_bst_region',
    'docsamson',
    'best_mmm',
    'get_hemisphere_and_base',
    'map_idps_to_rois',
    
    # qc_advanced
    'mm_match_by_qc_scoring',
    'mm_match_by_qc_scoring_all',
    'fix_LR_RL_stuff',
    'check_pd_construction',
    'shorten_pymm_names',
    'shorten_pymm_names2',
    
    # registration
    'dti_reg',
    'timeseries_reg',
    'mc_reg',
    'transform_and_reorient_dti',
    'apply_transforms_mixed_interpolation'
]

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

def remove_extracted_functions():
    """Remove all extracted functions from mm.py"""
    
    # Read the file
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    original_line_count = len(lines)
    print(f"Original file: {original_line_count} lines")
    
    # Find all function bounds
    functions_to_remove = []
    for func_name in extracted_functions:
        start, end = find_function_bounds(lines, func_name)
        if start is not None:
            functions_to_remove.append((func_name, start, end))
            print(f"Found {func_name}: lines {start+1}-{end+1}")
        else:
            print(f"WARNING: {func_name} not found")
    
    # Sort by start line in reverse order so we can remove from bottom up
    functions_to_remove.sort(key=lambda x: x[1], reverse=True)
    
    # Remove functions from bottom to top to preserve line numbers
    lines_removed = 0
    for func_name, start, end in functions_to_remove:
        print(f"Removing {func_name} (lines {start+1}-{end+1})")
        del lines[start:end+1]
        lines_removed += (end - start + 1)
    
    # Write the modified file
    with open('antspymm/mm.py', 'w') as f:
        f.writelines(lines)
    
    new_line_count = len(lines)
    print(f"\nSummary:")
    print(f"Original size: {original_line_count} lines")
    print(f"New size: {new_line_count} lines") 
    print(f"Removed: {lines_removed} lines")
    print(f"Reduction: {(lines_removed/original_line_count)*100:.1f}%")
    print(f"Functions removed: {len(functions_to_remove)}")

if __name__ == '__main__':
    remove_extracted_functions()