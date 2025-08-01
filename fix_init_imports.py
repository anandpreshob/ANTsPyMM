#!/usr/bin/env python
"""
Fix __init__.py imports to use the new modular structure
"""

import re

# Mapping of extracted functions to their new module locations
function_mapping = {
    # Pipeline functions
    'get_data': 'from .pipeline.data_utils import get_data',
    'get_models': 'from .pipeline.data_utils import get_models', 
    'write_mm': 'from .pipeline.output_utils import write_mm',
    
    # Utils functions
    'ants_to_nibabel_affine': 'from .utils.transform_utils import ants_to_nibabel_affine',
    'nrg_filename_to_subjectvisit': 'from .utils.string_utils import nrg_filename_to_subjectvisit',
    'parse_nrg_filename': 'from .utils.string_utils import parse_nrg_filename',
    'validate_filename': 'from .utils.string_utils import validate_filename',
    'validate_modality': 'from .utils.string_utils import validate_modality',
    'nrg_format_path': 'from .utils.string_utils import nrg_format_path',
    'get_antsimage_keys': 'from .utils.data_utils import get_antsimage_keys',
    'convert_np_in_dict': 'from .utils.data_utils import convert_np_in_dict',
    'validate_nrg_file_format': 'from .utils.filesystem_utils import validate_nrg_file_format',
    'clean_tmp_directory': 'from .utils.filesystem_utils import clean_tmp_directory',
    'get_valid_modalities': 'from .utils.conversion_utils import get_valid_modalities',
    'nrg_2_bids': 'from .utils.conversion_utils import nrg_2_bids',
    'bids_2_nrg': 'from .utils.conversion_utils import bids_2_nrg',
    'dict_to_dataframe': 'from .utils.conversion_utils import dict_to_dataframe',
    'filter_columns_by_nan_percentage': 'from .utils.conversion_utils import filter_columns_by_nan_percentage',
    
    # I/O functions
    'mm_read': 'from .image_io_module.image_io import mm_read',
    'mm_read_to_3d': 'from .image_io_module.image_io import mm_read_to_3d',
    'image_write_with_thumbnail': 'from .image_io_module.image_io import image_write_with_thumbnail',
    'write_bvals_bvecs': 'from .image_io_module.dwi_io import write_bvals_bvecs',
    
    # Processing functions  
    'get_dti': 'from .processing.dti import get_dti',
    'bvec_reorientation': 'from .processing.dti import bvec_reorientation',
    'tsnr': 'from .processing.qc import tsnr',
    'dvars': 'from .processing.qc import dvars',
    'mask_snr': 'from .processing.qc import mask_snr',
    'slice_snr': 'from .processing.qc import slice_snr',
    'deformation_gradient_optimized': 'from .processing.transforms import deformation_gradient_optimized',
    'segment_timeseries_by_bvalue': 'from .processing.segmentation import segment_timeseries_by_bvalue',
    'segment_timeseries_by_meanvalue': 'from .processing.segmentation import segment_timeseries_by_meanvalue',
}

def fix_init_imports():
    """Update __init__.py to use modular imports"""
    
    init_file = 'antspymm/__init__.py'
    
    # Read the current file
    with open(init_file, 'r') as f:
        lines = f.readlines()
    
    # Find and replace imports for extracted functions
    new_lines = []
    imports_added = set()
    
    for line in lines:
        # Check if this line imports an extracted function
        replaced = False
        for func_name, new_import in function_mapping.items():
            if f'from .mm import {func_name}' in line.strip():
                # Replace with new import if we haven't added it yet
                if new_import not in imports_added:
                    new_lines.append(new_import + '\n')
                    imports_added.add(new_import)
                replaced = True
                break
        
        # If not replaced, keep the original line
        if not replaced:
            new_lines.append(line)
    
    # Write the updated file
    with open(init_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Updated {len(function_mapping)} imports in __init__.py")
    print("Updated imports:")
    for func, new_import in function_mapping.items():
        print(f"  {func} -> {new_import}")

if __name__ == '__main__':
    fix_init_imports()