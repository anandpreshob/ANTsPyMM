#!/usr/bin/env python
"""
Validation script to ensure refactoring preserves exact functionality.
Run this before and after refactoring to verify identical behavior.
"""

import os
import sys
import pickle
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime

# Add the parent directory to the path to import antspymm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_test_cases():
    """Generate test cases for pure utility functions"""
    return {
        'nrg_filename_to_subjectvisit': [
            ('PPMI-3000-20140410-T1w-000', '-'),
            ('PROJECT-12345-20230101-DTI-001', '-'),
            ('STUDY_001_20220515_rsfMRI_002', '_'),
        ],
        'parse_nrg_filename': [
            ('PPMI-3000-20140410-T1w-000', '-'),
            ('PROJECT-12345-20230101-DTI-001', '-'),
        ],
        'validate_filename': [
            ('test_file.nii.gz', ['test', 'file'], 'Invalid keywords'),
            ('good_bad_file.txt', ['good', 'nice'], 'Must contain valid keyword'),
        ],
        'validate_modality': [
            ('T1w', ['T1w', 'T2w', 'DTI']),
            ('DTI', ['T1w', 'T2w', 'DTI']),
        ],
        'extend_list_to_length': [
            ([1, 2, 3], 5, 0),
            (['a', 'b'], 4, 'x'),
            ([1.0, 2.0], 3, None),
        ],
        'get_first_item_as_string': [
            (pd.DataFrame({'col1': ['string_value'], 'col2': [123]}), 'col1'),
            (pd.DataFrame({'col1': ['string_value'], 'col2': [123]}), 'col2'),
            (pd.DataFrame({'col1': [456.789], 'col2': ['text']}), 'col1'),
        ],
        'nrg_format_path': [
            ('PPMI', '3000', '20140410', 'T1w', '000', '-'),
            ('PROJECT', '12345', '20230101', 'DTI', '001', '-'),
        ],
        'version': [
            (),  # No arguments
        ],
    }

def run_function_safely(module, func_name, args):
    """Run a function and return result or exception"""
    try:
        func = getattr(module, func_name)
        result = func(*args)
        return ('success', result)
    except Exception as e:
        return ('error', str(e))

def serialize_result(result):
    """Serialize result for comparison"""
    status, value = result
    if status == 'error':
        return hashlib.md5(value.encode()).hexdigest()
    
    # Handle different types
    if isinstance(value, dict):
        # Sort dictionary and convert to string
        sorted_items = sorted(value.items())
        return hashlib.md5(str(sorted_items).encode()).hexdigest()
    elif isinstance(value, (list, tuple)):
        return hashlib.md5(str(value).encode()).hexdigest()
    elif isinstance(value, pd.DataFrame):
        return hashlib.md5(value.to_csv().encode()).hexdigest()
    elif isinstance(value, np.ndarray):
        return hashlib.md5(value.tobytes()).hexdigest()
    else:
        return hashlib.md5(str(value).encode()).hexdigest()

def create_baseline(output_file='baseline_results.pkl'):
    """Create baseline results from current implementation"""
    import antspymm.mm as mm
    
    test_cases = generate_test_cases()
    results = {}
    
    print("Creating baseline fingerprints...")
    for func_name, cases in test_cases.items():
        print(f"  Testing {func_name}...")
        results[func_name] = []
        
        for case_args in cases:
            result = run_function_safely(mm, func_name, case_args)
            fingerprint = serialize_result(result)
            results[func_name].append({
                'args': case_args,
                'result': result,
                'fingerprint': fingerprint
            })
            print(f"    Case {case_args}: {fingerprint[:8]}...")
    
    # Save results
    with open(output_file, 'wb') as f:
        pickle.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f)
    
    print(f"\nBaseline saved to {output_file}")
    return results

def validate_against_baseline(baseline_file='baseline_results.pkl'):
    """Validate current implementation against baseline"""
    import antspymm.mm as mm
    
    # Load baseline
    with open(baseline_file, 'rb') as f:
        baseline_data = pickle.load(f)
    
    baseline_results = baseline_data['results']
    test_cases = generate_test_cases()
    
    all_passed = True
    detailed_results = []
    
    print(f"Validating against baseline from {baseline_data['timestamp']}...")
    
    for func_name, cases in test_cases.items():
        print(f"\n  Testing {func_name}...")
        func_passed = True
        
        for i, case_args in enumerate(cases):
            current_result = run_function_safely(mm, func_name, case_args)
            current_fingerprint = serialize_result(current_result)
            baseline_fingerprint = baseline_results[func_name][i]['fingerprint']
            
            passed = current_fingerprint == baseline_fingerprint
            func_passed = func_passed and passed
            
            status_symbol = '✓' if passed else '✗'
            print(f"    {status_symbol} Case {case_args}")
            
            if not passed:
                print(f"      Expected: {baseline_fingerprint[:16]}...")
                print(f"      Got:      {current_fingerprint[:16]}...")
                detailed_results.append({
                    'function': func_name,
                    'args': case_args,
                    'baseline': baseline_results[func_name][i]['result'],
                    'current': current_result
                })
        
        all_passed = all_passed and func_passed
    
    if all_passed:
        print("\n✓ All tests passed! Refactoring preserved functionality.")
    else:
        print("\n✗ Some tests failed. Review detailed results.")
        print("\nDetailed failures:")
        for failure in detailed_results:
            print(f"\n  Function: {failure['function']}")
            print(f"  Args: {failure['args']}")
            print(f"  Baseline: {failure['baseline']}")
            print(f"  Current:  {failure['current']}")
    
    return all_passed

def main():
    """Main validation workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate antspymm refactoring')
    parser.add_argument('--create-baseline', action='store_true',
                        help='Create baseline results from current implementation')
    parser.add_argument('--validate', action='store_true',
                        help='Validate current implementation against baseline')
    parser.add_argument('--baseline-file', default='baseline_results.pkl',
                        help='Path to baseline file')
    
    args = parser.parse_args()
    
    if args.create_baseline:
        create_baseline(args.baseline_file)
    elif args.validate:
        validate_against_baseline(args.baseline_file)
    else:
        print("Creating baseline first, then validating...")
        create_baseline(args.baseline_file)
        print("\n" + "="*60 + "\n")
        validate_against_baseline(args.baseline_file)

if __name__ == '__main__':
    main()