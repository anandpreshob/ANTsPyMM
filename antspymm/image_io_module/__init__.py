"""
I/O modules for ANTsPyMM - refactored from mm.py

This package contains input/output functions extracted from the monolithic mm.py file.
All functions maintain their original signatures and behavior.
"""

# Import all I/O functions to maintain backward compatibility
from .image_io import (
    mm_read,
    mm_read_to_3d,
    image_write_with_thumbnail
)

from .dwi_io import (
    write_bvals_bvecs
)

__all__ = [
    # Image I/O
    'mm_read',
    'mm_read_to_3d',
    'image_write_with_thumbnail',
    # DWI I/O
    'write_bvals_bvecs'
]