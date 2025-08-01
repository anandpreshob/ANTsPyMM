#!/usr/bin/env python
"""
Combined test script for all extracted functions (Phase 1, 2 & 3)
"""

import sys
import os

# Add the directory containing utils to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'antspymm'))

# Import test functions from individual test scripts
exec(open('test_utils_directly.py').read())
exec(open('test_filesystem_utils.py').read())
exec(open('test_conversion_utils.py').read())

def main_combined():
    """Run all tests for Phase 1, Phase 2, and Phase 3"""
    print("="*70)
    print("Testing ALL Extracted Functions (Phase 1, 2 & 3)")
    print("="*70)
    print()
    
    # Phase 1 tests
    print("PHASE 1: Pure Utility Functions")
    print("-"*40)
    test_string_utils()
    test_data_utils()
    test_transform_utils()
    
    # Phase 2 tests
    print("\nPHASE 2: Filesystem Utility Functions")
    print("-"*40)
    test_validate_nrg_file_format()
    test_find_most_recent_file()
    test_clean_tmp_directory()
    
    # Phase 3 tests
    print("\nPHASE 3: Data Conversion Functions")
    print("-"*40)
    test_get_valid_modalities()
    test_nrg_2_bids()
    test_bids_2_nrg()
    test_dict_to_dataframe()
    test_to_nibabel()
    
    print("\n" + "="*70)
    print("COMBINED TEST SUMMARY: All 19 extracted functions verified!")
    print("="*70)
    print("\nExtracted functions count:")
    print("  Phase 1: 11 functions")
    print("  Phase 2: 3 functions")
    print("  Phase 3: 5 functions")
    print("  Total: 19 functions")

if __name__ == '__main__':
    main_combined()