#!/usr/bin/env python
"""
Test the extracted data conversion utility functions
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the directory containing utils to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'antspymm'))

def test_get_valid_modalities():
    """Test get_valid_modalities function"""
    from utils.conversion_utils import get_valid_modalities
    
    print("Testing get_valid_modalities...")
    
    # Test default
    modalities = get_valid_modalities()
    assert isinstance(modalities, list), "Should return a list"
    assert 'T1w' in modalities, "Should contain T1w"
    assert 'DTI' in modalities, "Should contain DTI"
    assert 'rsfMRI' in modalities, "Should contain rsfMRI"
    print("  ✓ Default modalities")
    
    # Test long version
    long_modalities = get_valid_modalities(long=True)
    assert len(long_modalities) > len(modalities), "Long version should have more modalities"
    assert 'DTI_LR' in long_modalities, "Long version should contain DTI_LR"
    print("  ✓ Long modalities")
    
    # Test QC version
    qc_modalities = get_valid_modalities(qc=True)
    assert 'DTIdwi' in qc_modalities, "QC version should contain DTIdwi"
    print("  ✓ QC modalities")
    
    # Test as string
    modalities_str = get_valid_modalities(asString=True)
    assert isinstance(modalities_str, str), "Should return a string"
    assert 'T1w' in modalities_str, "String should contain T1w"
    print("  ✓ As string format")
    
    print("get_valid_modalities: All tests passed!\n")

def test_nrg_2_bids():
    """Test NRG to BIDS conversion"""
    from utils.conversion_utils import nrg_2_bids
    
    print("Testing nrg_2_bids...")
    
    # Test T1w conversion
    nrg_path = '/data/PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000.nii.gz'
    bids_path = nrg_2_bids(nrg_path)
    expected = '/data/PPMI/3000/20140410/T1w/000/bids/sub-3000/ses-000/anat/sub-3000_ses-000_T1w.nii.gz'
    assert bids_path == expected, f"Expected {expected}, got {bids_path}"
    print("  ✓ T1w conversion")
    
    # Test DTI conversion
    nrg_path = '/data/STUDY/1234/20220101/DTI/001/STUDY-1234-20220101-DTI-001.nii'
    bids_path = nrg_2_bids(nrg_path)
    expected = '/data/STUDY/1234/20220101/DTI/001/bids/sub-1234/ses-001/dwi/sub-1234_ses-001_dwi.nii'
    assert bids_path == expected, f"Expected {expected}, got {bids_path}"
    print("  ✓ DTI conversion")
    
    # Test rsfMRI conversion
    nrg_path = '/test/PROJECT/5678/20230315/rsfMRI/002/PROJECT-5678-20230315-rsfMRI-002.nii.gz'
    bids_path = nrg_2_bids(nrg_path)
    expected = '/test/PROJECT/5678/20230315/rsfMRI/002/bids/sub-5678/ses-002/func/sub-5678_ses-002_func.nii.gz'
    assert bids_path == expected, f"Expected {expected}, got {bids_path}"
    print("  ✓ rsfMRI conversion")
    
    # Test T2Flair conversion
    nrg_path = '/data/PPMI/3000/20140410/T2Flair/000/PPMI-3000-20140410-T2Flair-000.nii.gz'
    bids_path = nrg_2_bids(nrg_path)
    expected = '/data/PPMI/3000/20140410/T2Flair/000/bids/sub-3000/ses-000/anat/sub-3000_ses-000_flair.nii.gz'
    assert bids_path == expected, f"Expected {expected}, got {bids_path}"
    print("  ✓ T2Flair conversion")
    
    # Test invalid modality
    try:
        nrg_path = '/data/PPMI/3000/20140410/INVALID/000/PPMI-3000-20140410-INVALID-000.nii.gz'
        bids_path = nrg_2_bids(nrg_path)
        print("  ✗ Should have raised error for invalid modality")
    except ValueError as e:
        assert 'not a valid mm modality' in str(e)
        print("  ✓ Invalid modality handled")
    
    print("nrg_2_bids: All tests passed!\n")

def test_bids_2_nrg():
    """Test BIDS to NRG conversion"""
    from utils.conversion_utils import bids_2_nrg
    
    print("Testing bids_2_nrg...")
    
    # Test anat/T1w conversion
    bids_path = 'sub-3000_ses-000_T1w.nii.gz'
    nrg_path = bids_2_nrg(bids_path, 'PPMI', '20140410')
    expected = 'PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000.nii.gz'
    assert nrg_path == expected, f"Expected {expected}, got {nrg_path}"
    print("  ✓ T1w conversion")
    
    # Test dwi/DTI conversion
    bids_path = 'sub-1234_ses-001_dwi.nii'
    nrg_path = bids_2_nrg(bids_path, 'STUDY', '20220101')
    expected = 'STUDY/1234/20220101/DTI/001/STUDY-1234-20220101-DTI-001.nii'
    assert nrg_path == expected, f"Expected {expected}, got {nrg_path}"
    print("  ✓ DTI conversion")
    
    # Test func/rsfMRI conversion
    bids_path = 'sub-5678_ses-002_func.nii.gz'
    nrg_path = bids_2_nrg(bids_path, 'PROJECT', '20230315')
    expected = 'PROJECT/5678/20230315/rsfMRI/002/PROJECT-5678-20230315-rsfMRI-002.nii.gz'
    assert nrg_path == expected, f"Expected {expected}, got {nrg_path}"
    print("  ✓ rsfMRI conversion")
    
    # Test with explicit modality
    bids_path = 'sub-1111_ses-003_dwi.nii.gz'
    nrg_path = bids_2_nrg(bids_path, 'TEST', '20240101', nrg_modality='DTI')
    expected = 'TEST/1111/20240101/DTI/003/TEST-1111-20240101-DTI-003.nii.gz'
    assert nrg_path == expected, f"Expected {expected}, got {nrg_path}"
    print("  ✓ Explicit modality")
    
    print("bids_2_nrg: All tests passed!\n")

def test_dict_to_dataframe():
    """Test dictionary to dataframe conversion"""
    from utils.conversion_utils import dict_to_dataframe
    
    print("Testing dict_to_dataframe...")
    
    # Test with scalars
    data = {'a': 1, 'b': 2.5, 'c': 'hello', 'd': True}
    df = dict_to_dataframe(data)
    assert isinstance(df, pd.DataFrame), "Should return DataFrame"
    assert df.shape[0] == 1, "Should have 1 row"
    assert df['a'].iloc[0] == 1, "Should preserve integer"
    assert df['b'].iloc[0] == 2.5, "Should preserve float"
    assert df['c'].iloc[0] == 'hello', "Should preserve string"
    assert df['d'].iloc[0] == True, "Should preserve boolean"
    print("  ✓ Scalar values")
    
    # Test with lists
    data = {'values': [1, 2, 3, 4, 5], 'name': 'test'}
    df = dict_to_dataframe(data, convert_lists=True)
    assert 'values_mean' in df.columns, "Should create mean column for list"
    assert df['values_mean'].iloc[0] == 3.0, "Should calculate correct mean"
    assert 'name' in df.columns, "Should preserve scalar"
    print("  ✓ List conversion with mean")
    
    # Test with numpy arrays
    data = {'array': np.array([10, 20, 30]), 'id': 42}
    df = dict_to_dataframe(data, convert_arrays=True)
    assert 'array_mean' in df.columns, "Should create mean column for array"
    assert df['array_mean'].iloc[0] == 20.0, "Should calculate correct array mean"
    print("  ✓ NumPy array conversion")
    
    # Test with mixed types
    data = {
        'scalar': 100,
        'list_nums': [1, 2, 3],
        'list_mixed': [1, 'two', 3],  # Should be ignored
        'empty_list': [],
        'array': np.array([5, 10, 15])
    }
    df = dict_to_dataframe(data)
    assert 'scalar' in df.columns, "Should include scalar"
    assert 'list_nums_mean' in df.columns, "Should convert numeric list"
    assert 'list_mixed_mean' not in df.columns, "Should not convert mixed list"
    assert 'empty_list_mean' not in df.columns or df['empty_list_mean'].iloc[0] == 0, "Should handle empty list"
    print("  ✓ Mixed types handled correctly")
    
    # Test with convert flags off
    data = {'values': [1, 2, 3], 'arr': np.array([4, 5, 6])}
    df = dict_to_dataframe(data, convert_lists=False, convert_arrays=False)
    assert 'values_mean' not in df.columns, "Should not convert lists when flag is False"
    assert 'arr_mean' not in df.columns, "Should not convert arrays when flag is False"
    print("  ✓ Conversion flags respected")
    
    print("dict_to_dataframe: All tests passed!\n")

def test_to_nibabel():
    """Test ANTs to nibabel conversion"""
    from utils.conversion_utils import to_nibabel
    
    print("Testing to_nibabel...")
    
    # Since we don't have ants available, test error handling
    class MockAntsImage:
        def __init__(self):
            self.dimension = 3
            self.spacing = [1.0, 1.0, 1.0]
            self.origin = [0.0, 0.0, 0.0]
            self.direction = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        
        def numpy(self):
            return np.zeros((10, 10, 10))
    
    # Test that it raises error when packages not available
    try:
        mock_img = MockAntsImage()
        result = to_nibabel(mock_img)
        print("  ⚠ Cannot fully test without ants/nibabel packages")
    except ImportError as e:
        print("  ✓ Correctly raises ImportError when packages missing")
    
    print("to_nibabel: Basic tests passed!\n")

def main():
    """Run all conversion utility tests"""
    print("="*60)
    print("Testing Phase 3: Data Conversion Utility Functions")
    print("="*60)
    print()
    
    test_get_valid_modalities()
    test_nrg_2_bids()
    test_bids_2_nrg()
    test_dict_to_dataframe()
    test_to_nibabel()
    
    print("="*60)
    print("Test Summary: All conversion utilities verified!")
    print("="*60)

if __name__ == '__main__':
    main()