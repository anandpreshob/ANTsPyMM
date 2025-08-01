#!/usr/bin/env python
"""
Analyze remaining functions in mm.py to identify extraction candidates
"""

import re

def analyze_remaining_functions():
    """Find all remaining functions in mm.py and their sizes"""
    
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
    
    print(f"Remaining functions in mm.py: {len(functions)}")
    print("=" * 70)
    print(f"{'Function Name':<40} {'Lines':<8} {'Start':<8} {'End':<8}")
    print("=" * 70)
    
    total_function_lines = 0
    large_functions = []
    
    for func_name, start, end, size in functions:
        print(f"{func_name:<40} {size:<8} {start+1:<8} {end+1:<8}")
        total_function_lines += size
        
        # Mark functions over 50 lines as candidates for extraction
        if size >= 50:
            large_functions.append((func_name, start, end, size))
    
    print("=" * 70)
    print(f"Total lines in functions: {total_function_lines}")
    print(f"Total file lines: {len(lines)}")
    print(f"Non-function lines: {len(lines) - total_function_lines}")
    
    print(f"\nLarge functions (>=50 lines) - EXTRACTION CANDIDATES:")
    print("=" * 50)
    for func_name, start, end, size in large_functions:
        print(f"{func_name}: {size} lines")
    
    print(f"\nTotal extractable function lines: {sum(f[3] for f in large_functions)}")
    estimated_reduction = sum(f[3] for f in large_functions)
    estimated_new_size = len(lines) - estimated_reduction
    print(f"Estimated new mm.py size after extraction: {estimated_new_size} lines")
    print(f"That would be a {(estimated_reduction/len(lines))*100:.1f}% reduction")
    
    return large_functions

if __name__ == '__main__':
    large_functions = analyze_remaining_functions()