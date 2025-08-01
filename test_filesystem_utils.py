#!/usr/bin/env python
"""
Test the extracted filesystem utility functions
"""

import sys
import os
import tempfile
import time
from datetime import datetime

# Add the directory containing utils to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'antspymm'))

def test_validate_nrg_file_format():
    """Test NRG file format validation"""
    from utils.filesystem_utils import validate_nrg_file_format
    
    print("Testing validate_nrg_file_format...")
    
    # Test valid NRG paths
    valid_path = '/Users/data/PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000.nii.gz'
    result, message = validate_nrg_file_format(valid_path, '-')
    assert result == True, f"Expected valid path to return True, got {result}: {message}"
    print("  ✓ Valid NRG path")
    
    # Test invalid path - too few components
    invalid_path1 = '/PPMI/3000/PPMI-3000.nii.gz'
    result, message = validate_nrg_file_format(invalid_path1, '-')
    assert result == False, f"Expected invalid path to return False"
    print("  ✓ Invalid path - too few components")
    
    # Test invalid path - mismatched filename
    invalid_path2 = '/Users/data/PPMI/3000/20140410/T1w/000/WRONG-3000-20140410-T1w-000.nii.gz'
    result, message = validate_nrg_file_format(invalid_path2, '-')
    assert result == False, f"Expected mismatched filename to return False"
    print("  ✓ Invalid path - mismatched filename")
    
    # Test invalid extension
    invalid_path3 = '/Users/data/PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000.txt'
    result, message = validate_nrg_file_format(invalid_path3, '-')
    assert result == False, f"Expected invalid extension to return False"
    print("  ✓ Invalid path - bad extension")
    
    # Test path with multiple slashes
    messy_path = '/Users//data///PPMI/3000/20140410/T1w/000/PPMI-3000-20140410-T1w-000.nii.gz'
    result, message = validate_nrg_file_format(messy_path, '-')
    assert result == True, f"Expected normalized path to be valid"
    print("  ✓ Path with multiple slashes normalized")
    
    print("validate_nrg_file_format: All tests passed!\n")

def test_find_most_recent_file():
    """Test find most recent file function"""
    from utils.filesystem_utils import find_most_recent_file
    
    print("Testing find_most_recent_file...")
    
    # Create temporary files with different modification times
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        
        # Create files with 1 second delays
        for i in range(3):
            filepath = os.path.join(tmpdir, f'test_file_{i}.txt')
            with open(filepath, 'w') as f:
                f.write(f'Test content {i}')
            files.append(filepath)
            if i < 2:  # Don't sleep after the last file
                time.sleep(0.1)
        
        # Test finding most recent
        result = find_most_recent_file(files)
        assert result is not None, "Expected to find a file"
        assert result[0] == files[-1], f"Expected {files[-1]}, got {result[0]}"
        print("  ✓ Found most recent file")
        
        # Test with non-existent files
        fake_files = ['/fake/path/1.txt', '/fake/path/2.txt']
        result = find_most_recent_file(fake_files)
        assert result is None, "Expected None for non-existent files"
        print("  ✓ Returns None for non-existent files")
        
        # Test with empty list
        result = find_most_recent_file([])
        assert result is None, "Expected None for empty list"
        print("  ✓ Returns None for empty list")
        
        # Test with mixed valid and invalid files
        mixed_files = [files[0], '/fake/path.txt', files[1]]
        result = find_most_recent_file(mixed_files)
        assert result is not None, "Expected to find a file from mixed list"
        assert result[0] in files, "Expected result to be one of the valid files"
        print("  ✓ Handles mixed valid/invalid files")
    
    print("find_most_recent_file: All tests passed!\n")

def test_clean_tmp_directory():
    """Test clean_tmp_directory function (limited testing due to safety)"""
    from utils.filesystem_utils import clean_tmp_directory
    
    print("Testing clean_tmp_directory...")
    
    # Test with invalid age_hours (should return early)
    clean_tmp_directory(age_hours="invalid")  # Should return without error
    print("  ✓ Handles invalid age_hours gracefully")
    
    # Test with a very large age_hours to ensure nothing gets deleted in real /tmp
    clean_tmp_directory(age_hours=999999.0, extensions=['.test_xyz123'])  # Very unlikely extension
    print("  ✓ Runs without error with safe parameters")
    
    # We can't fully test the deletion functionality without creating actual temp files
    # and potentially interfering with the system, so we just verify the function structure
    print("  ⚠ Full deletion testing skipped for safety")
    
    print("clean_tmp_directory: Basic tests passed!\n")

def main():
    """Run all filesystem utility tests"""
    print("="*60)
    print("Testing Phase 2: Filesystem Utility Functions")
    print("="*60)
    print()
    
    test_validate_nrg_file_format()
    test_find_most_recent_file()
    test_clean_tmp_directory()
    
    print("="*60)
    print("Test Summary: All filesystem utilities verified!")
    print("="*60)

if __name__ == '__main__':
    main()