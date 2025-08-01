# Pure Utility Functions for Initial Extraction

These functions are the safest to extract first as they:
- Have no side effects
- Don't modify global state
- Don't perform I/O operations
- Have minimal dependencies

## List of Functions to Extract in Phase 1:

### 1. String/Path Manipulation
```python
def nrg_filename_to_subjectvisit(s, separator='-')
def parse_nrg_filename(x, separator='-')
def validate_filename(filename, valid_keywords, error_message)
def validate_modality(modality, valid_modalities) 
def nrg_format_path(projectID, subjectID, date, modality, imageID, separator='-')
```

### 2. Data Structure Utilities
```python
def extend_list_to_length(lst, target_length, fill_value=None)
def get_antsimage_keys(dictionary)
def get_first_item_as_string(df, column_name)
def convert_np_in_dict(data_dict)
```

### 3. Mathematical/Transform Utilities
```python
def ants_to_nibabel_affine(ants_img)
```

### 4. Version Information
```python
def version()
```

## Dependencies for Each Function:

1. **nrg_filename_to_subjectvisit**: os.path.basename
2. **parse_nrg_filename**: None (pure Python)
3. **validate_filename**: None (pure Python)
4. **validate_modality**: None (pure Python)
5. **nrg_format_path**: os.path.join
6. **extend_list_to_length**: None (pure Python)
7. **get_antsimage_keys**: ants.core.ants_image.ANTsImage (for type check only)
8. **get_first_item_as_string**: pandas (for DataFrame access)
9. **convert_np_in_dict**: numpy
10. **ants_to_nibabel_affine**: numpy
11. **version**: pkg_resources

## Proposed Module Structure:

```
antspymm/
├── mm.py (original, will import from new modules)
├── utils/
│   ├── __init__.py
│   ├── string_utils.py (functions 1-5)
│   ├── data_utils.py (functions 6-9)
│   ├── transform_utils.py (function 10)
│   └── version_utils.py (function 11)
```

## Validation Strategy:

1. Create test cases for each function with known inputs/outputs
2. Extract functions to new modules
3. Import in mm.py from new locations
4. Run test cases to ensure identical behavior
5. Keep original functions commented out until all tests pass