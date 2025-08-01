#!/usr/bin/env python
"""
Script to modify mm.py to import extracted functions from utils modules
while preserving all other code exactly as is.
"""

import re

# Functions that have been extracted to utils modules
EXTRACTED_FUNCTIONS = {
    'nrg_filename_to_subjectvisit': 'utils.string_utils',
    'parse_nrg_filename': 'utils.string_utils',
    'validate_filename': 'utils.string_utils',
    'validate_modality': 'utils.string_utils',
    'nrg_format_path': 'utils.string_utils',
    'extend_list_to_length': 'utils.data_utils',
    'get_antsimage_keys': 'utils.data_utils',
    'get_first_item_as_string': 'utils.data_utils',
    'convert_np_in_dict': 'utils.data_utils',
    'ants_to_nibabel_affine': 'utils.transform_utils',
    'version': 'utils.version_utils',
}

def create_import_statements():
    """Generate import statements for the extracted functions"""
    imports = []
    
    # Group by module
    modules = {}
    for func, module in EXTRACTED_FUNCTIONS.items():
        if module not in modules:
            modules[module] = []
        modules[module].append(func)
    
    # Create import statements
    for module, funcs in sorted(modules.items()):
        if len(funcs) == 1:
            imports.append(f"from antspymm.{module} import {funcs[0]}")
        else:
            func_list = ", ".join(sorted(funcs))
            imports.append(f"from antspymm.{module} import ({func_list})")
    
    return "\n".join(imports)

def comment_out_function(content, func_name):
    """Comment out a function definition in the content"""
    # Find the function definition
    pattern = rf'^def {func_name}\s*\([^)]*\)\s*:'
    
    lines = content.split('\n')
    result = []
    in_function = False
    function_indent = None
    
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            in_function = True
            function_indent = len(line) - len(line.lstrip())
            result.append('# ' + line + '  # Moved to utils')
        elif in_function:
            # Check if we're still in the function
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # We've reached the next top-level statement
                in_function = False
                function_indent = None
                result.append(line)
            elif line.strip() and function_indent is not None:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= function_indent and line.strip() and not line[function_indent:].startswith(' '):
                    # We've reached the next function or statement at the same level
                    in_function = False
                    function_indent = None
                    result.append(line)
                else:
                    # Still in the function, comment it out
                    result.append('# ' + line)
            else:
                # Empty line or continuation of function
                result.append('# ' + line if line.strip() else '#')
        else:
            result.append(line)
    
    return '\n'.join(result)

def modify_mm_file(input_file='antspymm/mm.py', output_file='antspymm/mm_modified.py'):
    """Modify mm.py to use extracted utilities"""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Add imports after the existing imports
    import_marker = "from multiprocessing import Pool\nimport glob as glob"
    import_statements = create_import_statements()
    
    # Insert new imports after existing imports
    content = content.replace(
        import_marker,
        import_marker + "\n\n# Import utilities from refactored modules\n" + import_statements
    )
    
    # Comment out the extracted functions
    for func_name in EXTRACTED_FUNCTIONS:
        print(f"Commenting out {func_name}...")
        content = comment_out_function(content, func_name)
    
    # Write the modified content
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"\nModified file written to {output_file}")
    print("Review the changes and then replace mm.py with the modified version.")

if __name__ == '__main__':
    modify_mm_file()