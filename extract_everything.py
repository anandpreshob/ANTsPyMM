#!/usr/bin/env python
"""
Extract EVERYTHING except core pipeline functions
"""

import os
import re
import shutil

# Core functions to keep in mm.py
CORE_FUNCTIONS = ['mm', 'mm_csv', 'mm_nrg']

def find_all_functions(lines):
    """Find all function definitions in the file"""
    functions = []
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def '):
            func_match = re.match(r'def\s+(\w+)\s*\(', line.strip())
            if func_match:
                func_name = func_match.group(1)
                if func_name not in CORE_FUNCTIONS:
                    # Find function end
                    def_indent = len(lines[i]) - len(lines[i].lstrip())
                    
                    for j in range(i + 1, len(lines)):
                        line_j = lines[j]
                        
                        if not line_j.strip() or line_j.strip().startswith('#'):
                            continue
                            
                        current_indent = len(line_j) - len(line_j.lstrip())
                        
                        if current_indent <= def_indent:
                            if (line_j.strip().startswith('def ') or 
                                line_j.strip().startswith('class ') or
                                line_j.strip().startswith('import ') or
                                line_j.strip().startswith('from ') or
                                re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line_j.strip()) or
                                line_j.strip().startswith('__all__')):
                                functions.append((func_name, i, j - 1))
                                break
                    else:
                        functions.append((func_name, i, len(lines) - 1))
    
    return functions

def categorize_functions(functions, lines):
    """Categorize functions by their apparent purpose"""
    categories = {
        'image_processing': [],
        'data_processing': [],
        'utility': [],
        'analysis': [],
        'visualization': [],
        'io_utils': [],
        'stats': [],
        'dwi': []
    }
    
    for func_name, start, end in functions:
        size = end - start + 1
        
        # Categorize based on function name
        if any(keyword in func_name.lower() for keyword in ['image', 'neuromelanin', 'wmh', 'bold', 'template', 'crop']):
            categories['image_processing'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['dataframe', 'aggregate', 'merge', 'assemble']):
            categories['data_processing'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['plot', 'viz', 'figure', 'brainmap']):
            categories['visualization'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['dwi', 'dti', 'bvec', 'tensor']):
            categories['dwi'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['novelty', 'estimate', 'calculate', 'score']):
            categories['analysis'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['read', 'write', 'nrg']):
            categories['io_utils'].append((func_name, start, end, size))
        elif any(keyword in func_name.lower() for keyword in ['spec', 'alff', 'despike']):
            categories['stats'].append((func_name, start, end, size))
        else:
            categories['utility'].append((func_name, start, end, size))
    
    return categories

def extract_all_functions():
    """Extract all non-core functions"""
    
    # Create backup
    shutil.copy2('antspymm/mm.py', 'antspymm/mm.py.before_final_extraction')
    print("Created backup: antspymm/mm.py.before_final_extraction")
    
    # Read mm.py
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    original_size = len(lines)
    print(f"Current mm.py size: {original_size} lines")
    
    # Find all functions
    functions = find_all_functions(lines)
    print(f"Found {len(functions)} functions to extract")
    
    # Categorize functions
    categories = categorize_functions(functions, lines)
    
    # Create modules and extract functions
    for category, func_list in categories.items():
        if func_list:
            print(f"\nExtracting {category} functions ({len(func_list)} functions)...")
            
            # Create module directory
            module_dir = f'antspymm/{category}'
            os.makedirs(module_dir, exist_ok=True)
            
            # Create module file
            module_file = f'{module_dir}/{category}.py'
            with open(module_file, 'w') as f:
                f.write(f'"""\n{category.replace("_", " ").title()} functions for ANTsPyMM\n')
                f.write('Extracted from mm.py - maintains exact original functionality\n"""\n\n')
                f.write('import os\nimport numpy as np\nimport pandas as pd\n\n')
                f.write('try:\n    import ants\nexcept ImportError:\n    ants = None\n\n')
                
                # Write functions
                func_list.sort(key=lambda x: x[1])  # Sort by start line
                for func_name, start, end, size in func_list:
                    func_lines = lines[start:end+1]
                    f.write(f'\n# {func_name} - {size} lines\n')
                    f.writelines(func_lines)
                    f.write('\n')
            
            # Create __init__.py
            init_file = f'{module_dir}/__init__.py'
            with open(init_file, 'w') as f:
                f.write(f'"""{category.replace("_", " ").title()} module for ANTsPyMM"""\n\n')
                f.write(f'from .{category} import (\n')
                for func_name, _, _, _ in func_list:
                    f.write(f'    {func_name},\n')
                f.write(')\n\n')
                f.write('__all__ = [\n')
                for func_name, _, _, _ in func_list:
                    f.write(f'    "{func_name}",\n')
                f.write(']\n')
    
    # Calculate total lines to remove
    all_functions = []
    for func_list in categories.values():
        all_functions.extend(func_list)
    
    total_lines = sum(f[3] for f in all_functions)
    
    print(f"\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Functions to extract: {len(all_functions)}")
    print(f"Lines to remove: {total_lines}")
    print(f"Estimated new size: {original_size - total_lines} lines")
    print(f"Reduction: {(total_lines/original_size)*100:.1f}%")
    
    return all_functions

def remove_all_functions(functions):
    """Remove all extracted functions from mm.py"""
    
    # Read the file
    with open('antspymm/mm.py', 'r') as f:
        lines = f.readlines()
    
    original_line_count = len(lines)
    
    # Sort by start line in reverse order
    functions.sort(key=lambda x: x[1], reverse=True)
    
    # Remove functions
    for func_name, start, end, size in functions:
        del lines[start:end+1]
    
    # Write the modified file
    with open('antspymm/mm.py', 'w') as f:
        f.writelines(lines)
    
    new_line_count = len(lines)
    print(f"\nFinal Results:")
    print(f"Original size: {original_line_count} lines")
    print(f"New size: {new_line_count} lines")
    print(f"Removed: {original_line_count - new_line_count} lines")
    print(f"Total reduction: {((original_line_count - new_line_count)/original_line_count)*100:.1f}%")

if __name__ == '__main__':
    # Extract all functions
    functions = extract_all_functions()
    
    # Remove them from mm.py
    if input(f"\nProceed with removing {len(functions)} functions? (y/n): ").lower() == 'y':
        remove_all_functions(functions)