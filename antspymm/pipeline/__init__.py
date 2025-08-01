"""
Pipeline modules for ANTsPyMM - refactored from mm.py

This package contains the main pipeline functions and utilities extracted from the monolithic mm.py file.
All functions maintain their original signatures and behavior.
"""

# Import data and model utilities
from .data_utils import get_data, get_models

# Import output utilities
from .output_utils import write_mm

# Import main pipeline functions from mm.py (keeping them in mm.py for now due to complexity)
from ..mm import mm, mm_csv, mm_nrg

__all__ = [
    # Data utilities
    'get_data',
    'get_models',
    # Output utilities
    'write_mm',
    # Main pipeline functions
    'mm',
    'mm_csv', 
    'mm_nrg'
]