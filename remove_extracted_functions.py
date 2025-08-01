#!/usr/bin/env python
"""
Remove extracted functions from mm.py to reduce file size
"""

import re
import shutil

# List of all extracted functions in order of extraction
extracted_functions = [
    # Phase 1: Utils
    'nrg_filename_to_subjectvisit',
    'parse_nrg_filename', 
    'validate_filename',
    'validate_modality',
    'nrg_format_path',
    'extend_list_to_length',
    'get_antsimage_keys',
    'ants_to_nibabel_affine',
    'convert_np_in_dict',
    'get_first_item_as_string',
    # Phase 2: Filesystem  
    'validate_nrg_file_format',
    'find_most_recent_file',
    'clean_tmp_directory',
    # Phase 3: Conversion
    'get_valid_modalities',
    'nrg_2_bids',
    'bids_2_nrg',
    'dict_to_dataframe', 
    'to_nibabel',
    'filter_columns_by_nan_percentage',
    # Phase 4: I/O
    'mm_read',
    'mm_read_to_3d',
    'image_write_with_thumbnail',
    'write_bvals_bvecs',
    # Phase 5: Processing
    'tsnr',
    'dvars',
    'mask_snr',
    'slice_snr',
    'foreground_background_snr',
    'quantile_snr',
    'bvec_reorientation',
    'get_dti',
    'deformation_gradient_optimized',
    'segment_timeseries_by_bvalue',
    'segment_timeseries_by_meanvalue',
    # Phase 6: Pipeline
    'get_data',
    'get_models', 
    'write_mm'
]

def find_function_bounds(lines, func_name):
    """Find the exact start and end lines of a function definition"""
    start_line = None
    
    # Find function start
    for i, line in enumerate(lines):
        if re.match(rf'def\s+{re.escape(func_name)}\s*\(', line.strip()):
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

def remove_functions_from_mm():
    """Remove all extracted functions from mm.py"""
    mm_file = 'antspymm/mm.py'
    backup_file = 'antspymm/mm.py.before_removal'
    
    # Create backup
    shutil.copy2(mm_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    # Read the file
    with open(mm_file, 'r') as f:
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
    with open(mm_file, 'w') as f:
        f.writelines(lines)
    
    new_line_count = len(lines)
    print(f"\nSummary:")
    print(f"Original size: {original_line_count} lines")
    print(f"New size: {new_line_count} lines") 
    print(f"Removed: {lines_removed} lines")
    print(f"Reduction: {(lines_removed/original_line_count)*100:.1f}%")
    print(f"Functions removed: {len(functions_to_remove)}")

if __name__ == '__main__':
    remove_functions_from_mm()