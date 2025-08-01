#!/usr/bin/env python
"""
Analyze ALL remaining functions in mm.py for aggressive extraction
"""

import re

def analyze_all_functions():
    """Find ALL functions remaining in mm.py, regardless of size"""
    
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    functions = []
    current_function = None
    current_start = None
    
    for i, line in enumerate(lines):
        # Look for function definitions
        if line.strip().startswith('def '):
            # Save previous function if exists
            if current_function and current_start is not None:
                functions.append((current_function, current_start, i-1, i-current_start))
            
            # Start new function
            func_match = re.match(r'def\s+(\w+)\s*\(', line.strip())
            if func_match:
                current_function = func_match.group(1)
                current_start = i
    
    # Don't forget the last function
    if current_function and current_start is not None:
        functions.append((current_function, current_start, len(lines)-1, len(lines)-current_start))
    
    # Sort by size (largest first)
    functions.sort(key=lambda x: x[3], reverse=True)
    
    print(f"ALL remaining functions in mm.py: {len(functions)}")
    print("=" * 80)
    print(f"{'Function Name':<40} {'Lines':<8} {'Start':<8} {'End':<8}")
    print("=" * 80)
    
    total_function_lines = 0
    core_pipeline_funcs = ['mm', 'mm_csv', 'mm_nrg']
    
    # Categorize functions
    large_functions = []  # >= 50 lines
    medium_functions = []  # 20-49 lines
    small_functions = []  # < 20 lines
    core_functions = []  # Core pipeline functions to keep
    
    for func_name, start, end, size in functions:
        print(f"{func_name:<40} {size:<8} {start+1:<8} {end+1:<8}")
        total_function_lines += size
        
        if func_name in core_pipeline_funcs:
            core_functions.append((func_name, start, end, size))
        elif size >= 50:
            large_functions.append((func_name, start, end, size))
        elif size >= 20:
            medium_functions.append((func_name, start, end, size))
        else:
            small_functions.append((func_name, start, end, size))
    
    print("=" * 80)
    print(f"Total lines in functions: {total_function_lines}")
    print(f"Total file lines: {len(lines)}")
    print(f"Non-function lines (imports, constants, etc.): {len(lines) - total_function_lines}")
    
    print(f"\nFunction breakdown:")
    print(f"  Core pipeline functions (KEEP): {len(core_functions)} functions, {sum(f[3] for f in core_functions)} lines")
    print(f"  Large functions (>=50 lines): {len(large_functions)} functions, {sum(f[3] for f in large_functions)} lines")
    print(f"  Medium functions (20-49 lines): {len(medium_functions)} functions, {sum(f[3] for f in medium_functions)} lines")
    print(f"  Small functions (<20 lines): {len(small_functions)} functions, {sum(f[3] for f in small_functions)} lines")
    
    # Calculate potential reduction
    extractable_lines = sum(f[3] for f in large_functions + medium_functions + small_functions)
    core_lines = sum(f[3] for f in core_functions)
    non_function_lines = len(lines) - total_function_lines
    
    print(f"\n" + "="*80)
    print("AGGRESSIVE EXTRACTION POTENTIAL")
    print("="*80)
    print(f"Current mm.py size: {len(lines)} lines")
    print(f"Core functions to keep: {core_lines} lines")
    print(f"Non-function lines: {non_function_lines} lines")
    print(f"Minimum possible size: {core_lines + non_function_lines} lines")
    print(f"Maximum extractable: {extractable_lines} lines")
    print(f"Potential new size: {len(lines) - extractable_lines} lines")
    print(f"Potential reduction: {(extractable_lines/len(lines))*100:.1f}%")
    
    # Print extraction plan
    print(f"\n" + "="*80)
    print("EXTRACTION PLAN FOR MAXIMUM REDUCTION")
    print("="*80)
    
    print("\nLARGE FUNCTIONS TO EXTRACT (>=50 lines):")
    for func_name, start, end, size in large_functions[:20]:  # Top 20
        print(f"  {func_name}: {size} lines")
    if len(large_functions) > 20:
        print(f"  ... and {len(large_functions) - 20} more")
        
    print("\nMEDIUM FUNCTIONS TO EXTRACT (20-49 lines):")
    for func_name, start, end, size in medium_functions[:10]:  # Top 10
        print(f"  {func_name}: {size} lines")
    if len(medium_functions) > 10:
        print(f"  ... and {len(medium_functions) - 10} more")
    
    return large_functions, medium_functions, small_functions, core_functions

if __name__ == '__main__':
    large, medium, small, core = analyze_all_functions()