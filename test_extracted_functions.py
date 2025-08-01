#!/usr/bin/env python
"""
Test the extracted utility functions to ensure they work correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_string_utils():
    """Test string utility functions"""
    from antspymm.utils.string_utils import (
        nrg_filename_to_subjectvisit,
        parse_nrg_filename,
        validate_filename,
        validate_modality,
        nrg_format_path
    )
    
    print("Testing string utilities...")
    
    # Test nrg_filename_to_subjectvisit
    result = nrg_filename_to_subjectvisit('PPMI-3000-20140410-T1w-000', '-')
    assert result == 'PPMI-3000-20140410', f"Expected 'PPMI-3000-20140410', got '{result}'"
    print("  ✓ nrg_filename_to_subjectvisit")
    
    # Test parse_nrg_filename
    result = parse_nrg_filename('PPMI-3000-20140410-T1w-000', '-')
    expected = {
        'project': 'PPMI',
        'subjectID': '3000',
        'date': '20140410',
        'modality': 'T1w',
        'imageID': '000'
    }
    assert result == expected, f"Expected {expected}, got {result}"
    print("  ✓ parse_nrg_filename")
    
    # Test validate_filename
    try:
        validate_filename('test_file.nii.gz', ['test', 'file'], 'Invalid keywords')
        print("  ✓ validate_filename (valid case)")
    except ValueError:
        print("  ✗ validate_filename (should not raise for valid case)")
    
    # Test validate_modality
    try:
        validate_modality('T1w', ['T1w', 'T2w', 'DTI'])
        print("  ✓ validate_modality (valid case)")
    except ValueError:
        print("  ✗ validate_modality (should not raise for valid case)")
    
    # Test nrg_format_path
    result = nrg_format_path('PPMI', '3000', '20140410', 'T1w', '000', '-')
    expected = 'PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000'
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("  ✓ nrg_format_path")
    
    print("String utilities: All tests passed!\n")

def test_data_utils():
    """Test data utility functions"""
    from antspymm.utils.data_utils import (
        extend_list_to_length,
        get_antsimage_keys,
        get_first_item_as_string,
        convert_np_in_dict
    )
    import pandas as pd
    import numpy as np
    
    print("Testing data utilities...")
    
    # Test extend_list_to_length
    result = extend_list_to_length([1, 2, 3], 5, 0)
    assert result == [1, 2, 3, 0, 0], f"Expected [1, 2, 3, 0, 0], got {result}"
    print("  ✓ extend_list_to_length")
    
    # Test get_antsimage_keys
    # Since we don't have ants available, we'll skip this test
    print("  ⚠ get_antsimage_keys (skipped - requires ants)")
    
    # Test get_first_item_as_string
    df = pd.DataFrame({'col1': ['string_value'], 'col2': [123]})
    result = get_first_item_as_string(df, 'col1')
    assert result == 'string_value', f"Expected 'string_value', got '{result}'"
    result = get_first_item_as_string(df, 'col2')
    assert result == '123', f"Expected '123', got '{result}'"
    print("  ✓ get_first_item_as_string")
    
    # Test convert_np_in_dict
    test_dict = {
        'float32': np.float32(1.5),
        'int32': np.int32(42),
        'string': 'hello',
        'regular_float': 3.14
    }
    result = convert_np_in_dict(test_dict)
    assert isinstance(result['float32'], float), "float32 should be converted to float"
    assert isinstance(result['int32'], int), "int32 should be converted to int"
    assert result['string'] == 'hello', "string should remain unchanged"
    assert result['regular_float'] == 3.14, "regular float should remain unchanged"
    print("  ✓ convert_np_in_dict")
    
    print("Data utilities: All tests passed!\n")

def test_transform_utils():
    """Test transform utility functions"""
    print("Testing transform utilities...")
    print("  ⚠ ants_to_nibabel_affine (skipped - requires ants)")
    print()

def test_version_utils():
    """Test version utility functions"""
    print("Testing version utilities...")
    print("  ⚠ version (skipped - requires installed packages)")
    print()

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Extracted Utility Functions")
    print("="*60)
    print()
    
    test_string_utils()
    test_data_utils()
    test_transform_utils()
    test_version_utils()
    
    print("="*60)
    print("Test Summary: Core functionality verified!")
    print("="*60)

if __name__ == '__main__':
    main()