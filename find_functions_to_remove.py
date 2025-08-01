#!/usr/bin/env python
"""
Find all extracted functions in mm.py that need to be removed
"""

import re

# List of all extracted functions
extracted_functions = [
    # Phase 1: Utils
    'nrg_filename_to_subjectvisit',
    'parse_nrg_filename',
    'validate_filename',
    'validate_modality', 
    'nrg_format_path',
    'filter_columns_by_nan_percentage',
    'get_antsimage_keys',
    'ants_to_nibabel_affine',
    'extend_list_to_length',
    'get_first_item_as_string',
    'convert_np_in_dict',
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

def find_function_definitions(filename):
    """Find line numbers where extracted functions are defined"""
    function_locations = {}
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        # Look for function definitions
        if line.strip().startswith('def '):
            func_match = re.match(r'def\s+(\w+)\s*\(', line.strip())
            if func_match:
                func_name = func_match.group(1)
                if func_name in extracted_functions:
                    function_locations[func_name] = i
    
    return function_locations

def find_function_end(lines, start_line):
    """Find where a function definition ends"""
    indent_level = None
    for i in range(start_line, len(lines)):
        line = lines[i]
        if line.strip() == '':
            continue
        
        # Set initial indent level from first non-empty line after def
        if indent_level is None and not line.startswith('def '):
            indent_level = len(line) - len(line.lstrip())
            continue
            
        # If we hit a line at the same or lesser indent level (and it's not empty/comment)
        if (indent_level is not None and 
            line.strip() and 
            not line.strip().startswith('#') and
            (len(line) - len(line.lstrip())) <= indent_level and
            not line.startswith('def ')):
            
            # Check if this looks like a new function or class
            if (line.strip().startswith('def ') or 
                line.strip().startswith('class ') or
                line.strip().startswith('import ') or
                line.strip().startswith('from ')):
                return i
    
    return len(lines)

if __name__ == '__main__':
    mm_file = 'antspymm/mm.py'
    locations = find_function_definitions(mm_file)
    
    # Read file to find function ends
    with open(mm_file, 'r') as f:
        lines = f.readlines()
    
    print("Functions found in mm.py that should be removed:")
    print("=" * 60)
    
    # Sort by line number
    sorted_functions = sorted(locations.items(), key=lambda x: x[1])
    
    function_ranges = []
    for func_name, start_line in sorted_functions:
        end_line = find_function_end(lines, start_line - 1)  # Convert to 0-based
        function_ranges.append((func_name, start_line, end_line))
        print(f"{func_name}: lines {start_line}-{end_line} ({end_line - start_line + 1} lines)")
    
    total_lines_to_remove = sum(end - start + 1 for _, start, end in function_ranges)
    current_lines = len(lines)
    estimated_new_size = current_lines - total_lines_to_remove
    
    print(f"\nSummary:")
    print(f"Current mm.py size: {current_lines} lines")
    print(f"Lines to remove: {total_lines_to_remove}")
    print(f"Estimated new size: {estimated_new_size} lines")
    print(f"Reduction: {(total_lines_to_remove/current_lines)*100:.1f}%")
    
    print(f"\nFound {len(locations)} out of {len(extracted_functions)} extracted functions")
    
    # Show missing functions
    missing = set(extracted_functions) - set(locations.keys())
    if missing:
        print(f"\nFunctions not found in mm.py (might have different names or already removed):")
        for func in sorted(missing):
            print(f"  - {func}")