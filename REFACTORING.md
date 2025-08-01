# ANTsPyMM Refactoring Documentation

## Overview
This document tracks the refactoring of `antspymm/mm.py` from a monolithic 13,000+ line file into a modular structure. The refactoring is designed to preserve exact functionality while improving code organization.

## Refactoring Principles
1. **No Logic Changes**: All functions maintain their exact original behavior
2. **Preserve Signatures**: All function signatures remain unchanged
3. **Backward Compatibility**: All public APIs remain accessible from their original locations
4. **Incremental Approach**: Extract safest functions first, validate at each step
5. **Parallel Structure**: New modules exist alongside original code during transition

## Phase 1: Pure Utility Functions (COMPLETED)

### Created Module Structure
```
antspymm/
├── mm.py (original, will import from new modules)
├── mm.py.backup (backup of original)
├── utils/
│   ├── __init__.py
│   ├── string_utils.py
│   ├── data_utils.py
│   ├── transform_utils.py
│   └── version_utils.py
```

### Functions Extracted

#### String Utilities (`utils/string_utils.py`)
1. **nrg_filename_to_subjectvisit(s, separator='-')**
   - Original location: mm.py:170-185
   - Purpose: Extract pattern from NRG filename
   - Dependencies: os.path

2. **parse_nrg_filename(x, separator='-')**
   - Original location: mm.py:972-985
   - Purpose: Parse NRG filename into components
   - Dependencies: None

3. **validate_filename(filename, valid_keywords, error_message)**
   - Original location: mm.py:828-842
   - Purpose: Validate filename contains valid keywords
   - Dependencies: None

4. **validate_modality(modality, valid_modalities)**
   - Original location: mm.py:843-846
   - Purpose: Validate modality against allowed values
   - Dependencies: None

5. **nrg_format_path(projectID, subjectID, date, modality, imageID, separator='-')**
   - Original location: mm.py:1180-1206
   - Purpose: Generate NRG format path
   - Dependencies: os.path

#### Data Utilities (`utils/data_utils.py`)
1. **extend_list_to_length(lst, target_length, fill_value=None)**
   - Original location: mm.py:848-849
   - Purpose: Extend list to target length
   - Dependencies: None

2. **get_antsimage_keys(dictionary)**
   - Original location: mm.py:366-373
   - Purpose: Extract ANTsImage keys from dictionary
   - Dependencies: ants (conditional import)

3. **get_first_item_as_string(df, column_name)**
   - Original location: mm.py:1209-1227
   - Purpose: Convert DataFrame first item to string
   - Dependencies: pandas

4. **convert_np_in_dict(data_dict)**
   - Original location: mm.py:1792-1807
   - Purpose: Convert numpy types to Python types
   - Dependencies: numpy

#### Transform Utilities (`utils/transform_utils.py`)
1. **ants_to_nibabel_affine(ants_img)**
   - Original location: mm.py:389-411
   - Purpose: Convert ANTs affine to nibabel format
   - Dependencies: numpy

#### Version Utilities (`utils/version_utils.py`)
1. **version()**
   - Original location: mm.py:144-168
   - Purpose: Report package versions
   - Dependencies: pkg_resources

## Validation Process

### Test Suite Created
1. **test_utils_directly.py**: Direct testing of extracted functions
   - Tests all extracted functions with known inputs/outputs
   - Validates behavior matches original implementation
   - All tests pass ✓

2. **validate_refactoring.py**: Comprehensive validation script
   - Creates baseline fingerprints before refactoring
   - Validates against baseline after refactoring
   - Supports incremental validation

3. **modify_mm_imports.py**: Automated import modification
   - Adds imports from new utility modules
   - Comments out original function definitions
   - Preserves all other code exactly

## Migration Instructions

### For Users
No changes required! All functions remain accessible from their original locations:
```python
import antspymm
# These all work as before:
antspymm.parse_nrg_filename(filename)
antspymm.mm.parse_nrg_filename(filename)
```

### For Developers
New imports are available for better organization:
```python
from antspymm.utils.string_utils import parse_nrg_filename
from antspymm.utils.data_utils import extend_list_to_length
```

## Next Phases

### Phase 2: File System Utilities
Target functions:
- validate_nrg_file_format()
- filter_image_files()
- clean_tmp_directory()

### Phase 3: Data Conversion Functions
Target functions:
- nrg_2_bids()
- bids_2_nrg()
- dict_to_dataframe()
- to_nibabel()

### Phase 4: I/O Functions
Target functions:
- mm_read()
- mm_read_to_3d()
- image_write_with_thumbnail()
- write_bvals_bvecs()

### Phase 5: Core Processing Functions
- Careful extraction of main pipeline functions
- May require creating additional modules for:
  - DTI processing
  - Registration functions
  - Quality control functions
  - Statistical functions

## Phase 2: File System Utilities (COMPLETED)

### Created Module
```
antspymm/
├── utils/
│   ├── filesystem_utils.py
```

### Functions Extracted

#### Filesystem Utilities (`utils/filesystem_utils.py`)
1. **validate_nrg_file_format(path, separator)**
   - Original location: mm.py:188-286
   - Purpose: Validate NRG file format compliance
   - Dependencies: os, re, warnings

2. **find_most_recent_file(file_list)**
   - Original location: mm.py:12407-12426
   - Purpose: Find most recently modified file from list
   - Dependencies: os

3. **clean_tmp_directory(age_hours, use_sudo, extensions, log_file_path)**
   - Original location: mm.py:468-518
   - Purpose: Clean temporary files based on age and extension
   - Dependencies: os, subprocess, datetime

### Validation Process
1. **test_filesystem_utils.py**: Created comprehensive tests
   - Tests NRG path validation with various cases
   - Tests file finding with temporary files
   - Tests clean function with safe parameters
   - All tests pass ✓

## Verification Checklist

- [x] Created backup of original mm.py
- [x] Extracted pure utility functions (Phase 1)
- [x] Extracted filesystem utilities (Phase 2)
- [x] Created test suite for extracted functions
- [x] All tests pass
- [x] Documentation created
- [ ] Modified mm.py to use new imports
- [ ] Run full test suite with modified mm.py
- [ ] Update package __init__.py if needed

## Notes

1. The `ants` dependency in `get_antsimage_keys` is handled with conditional import
2. All original comments and docstrings are preserved
3. Function order in modules matches logical grouping, not original file order
4. The DATA_PATH global variable remains in mm.py for now
5. Phase 2 adds 3 filesystem-related functions that are safe to extract