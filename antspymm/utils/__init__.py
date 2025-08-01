"""
Utility modules for ANTsPyMM - refactored from mm.py

This package contains utility functions extracted from the monolithic mm.py file.
All functions maintain their original signatures and behavior.
"""

# Import all utility functions to maintain backward compatibility
from .string_utils import (
    nrg_filename_to_subjectvisit,
    parse_nrg_filename,
    validate_filename,
    validate_modality,
    nrg_format_path
)

from .data_utils import (
    extend_list_to_length,
    get_antsimage_keys,
    get_first_item_as_string,
    convert_np_in_dict
)

from .transform_utils import (
    ants_to_nibabel_affine
)

from .version_utils import (
    version
)

__all__ = [
    # String utilities
    'nrg_filename_to_subjectvisit',
    'parse_nrg_filename', 
    'validate_filename',
    'validate_modality',
    'nrg_format_path',
    # Data utilities
    'extend_list_to_length',
    'get_antsimage_keys',
    'get_first_item_as_string',
    'convert_np_in_dict',
    # Transform utilities
    'ants_to_nibabel_affine',
    # Version utilities
    'version'
]