# ANTsPyMM Function Inventory

## Overview
This document lists all functions in `antspymm/mm.py` with their signatures and categorization for safe refactoring.

## Total Functions: 164

## Categories

### 1. Pure Utility Functions (Safe to Extract First)
These functions have no side effects and don't depend on global state:

1. **version()** - Reports package versions
   - No parameters
   - Returns: dictionary with package versions
   - Dependencies: pkg_resources only

2. **nrg_filename_to_subjectvisit(s, separator='-')** - Extract pattern from string
   - Pure string manipulation
   - No external dependencies

3. **parse_nrg_filename(x, separator='-')** - Parse NRG filename into parts
   - Pure string parsing
   - Returns: dictionary with filename components

4. **get_first_item_as_string(df, column_name)** - Convert first DataFrame item to string
   - Parameters: DataFrame and column name
   - Pure data extraction function

5. **validate_filename(filename, valid_keywords, error_message)** - Validate filename
   - Pure validation logic
   - No side effects

6. **validate_modality(modality, valid_modalities)** - Validate modality
   - Pure validation logic
   - No side effects

7. **extend_list_to_length(lst, target_length, fill_value=None)** - Extend list
   - Pure list manipulation
   - No side effects

8. **get_antsimage_keys(dictionary)** - Extract ANTsImage keys from dictionary
   - Pure dictionary inspection
   - Dependencies: ants.core.ants_image.ANTsImage type check

9. **ants_to_nibabel_affine(ants_img)** - Convert ANTs affine to nibabel format
   - Pure mathematical transformation
   - Dependencies: numpy

10. **convert_np_in_dict(data_dict)** - Convert numpy arrays in dictionary
    - Pure data transformation
    - Dependencies: numpy

### 2. File System Utility Functions (Extract Second)
These interact with file system but are still relatively isolated:

1. **validate_nrg_file_format(path, separator)** - Validate NRG file format
   - File path validation
   - No file I/O, just path string checking

2. **nrg_format_path(projectID, subjectID, date, modality, imageID, separator='-')** - Build NRG path
   - Pure path construction
   - Dependencies: os.path

3. **filter_image_files(files, modalities=None)** - Filter image files
   - Pure list filtering
   - No actual file I/O

### 3. Data Conversion Functions (Extract Third)
These perform data transformations but depend on external libraries:

1. **nrg_2_bids(nrg_filename)** - Convert NRG to BIDS format
   - Dependencies: get_valid_modalities()
   - Mostly string manipulation

2. **bids_2_nrg(bids_filename, project_name, date, nrg_modality=None)** - Convert BIDS to NRG
   - Dependencies: get_valid_modalities()
   - Mostly string manipulation

3. **dict_to_dataframe(data_dict, convert_lists=True, convert_arrays=True, convert_images=True, verbose=False)**
   - Convert dictionary to DataFrame
   - Dependencies: pandas, numpy, ants

4. **to_nibabel(img)** - Convert ANTs image to nibabel
   - Dependencies: nibabel, ants_to_nibabel_affine()

### 4. I/O Functions (Extract with Care)
These perform actual file I/O:

1. **mm_read(x, standardize_intensity=False, modality='')** - Read medical images
   - File I/O
   - Dependencies: ants.image_read

2. **mm_read_to_3d(x, slice=None, modality='')** - Read images to 3D
   - File I/O
   - Dependencies: ants.image_read

3. **image_write_with_thumbnail(x, fn, y=None, thumb=True)** - Write images with thumbnails
   - File I/O
   - Dependencies: ants, matplotlib

### 5. Core Processing Functions (Extract Last)
These contain the main pipeline logic and have complex dependencies:

1. **mm()** - Main processing pipeline
2. **mm_csv()** - CSV-based processing
3. **mm_nrg()** - NRG-based processing
4. **get_dti()** - DTI processing
5. **dti_reg()** - DTI registration
6. **mc_reg()** - Motion correction registration
7. And many others...

## Entry Points
Main public API functions that external users call:
- mm()
- mm_csv()
- mm_nrg()
- write_mm()
- get_data()
- get_models()
- version()

## Global State
- DATA_PATH = os.path.expanduser('~/.antspymm/')
- Random seed setting via antspyt1w

## Next Steps
1. Start extracting pure utility functions (Category 1)
2. Create test cases for these functions
3. Move to file system utilities (Category 2)
4. Progress through remaining categories

## Extraction Progress

### Phase 1: Pure Utility Functions (COMPLETED)
- [x] nrg_filename_to_subjectvisit - antspymm/utils/string_utils.py
- [x] parse_nrg_filename - antspymm/utils/string_utils.py
- [x] validate_filename - antspymm/utils/string_utils.py
- [x] validate_modality - antspymm/utils/string_utils.py
- [x] nrg_format_path - antspymm/utils/string_utils.py
- [x] filter_columns_by_nan_percentage - antspymm/utils/data_utils.py
- [x] dict_to_dataframe - antspymm/utils/data_utils.py
- [x] get_valid_modalities - antspymm/utils/data_utils.py
- [x] ants_matrix_to_rotation - antspymm/utils/transform_utils.py
- [x] closest_orthogonal_matrix - antspymm/utils/transform_utils.py
- [x] get_antsregistration_iterations - antspymm/utils/transform_utils.py

### Phase 2: Filesystem Utilities (COMPLETED)
- [x] validate_nrg_file_format - antspymm/utils/filesystem_utils.py
- [x] find_most_recent_file - antspymm/utils/filesystem_utils.py
- [x] clean_tmp_directory - antspymm/utils/filesystem_utils.py

### Phase 3: Data Conversion Functions (COMPLETED)
- [x] nrg_2_bids - antspymm/utils/conversion_utils.py
- [x] bids_2_nrg - antspymm/utils/conversion_utils.py
- [x] dict_to_dataframe - antspymm/utils/conversion_utils.py
- [x] to_nibabel - antspymm/utils/conversion_utils.py
- [x] get_valid_modalities - antspymm/utils/conversion_utils.py

### Phase 4: I/O Functions (COMPLETED)
- [x] mm_read - antspymm/image_io_module/image_io.py
- [x] mm_read_to_3d - antspymm/image_io_module/image_io.py
- [x] image_write_with_thumbnail - antspymm/image_io_module/image_io.py
- [x] write_bvals_bvecs - antspymm/image_io_module/dwi_io.py

### Phase 5: Processing Functions (COMPLETED)
- [x] tsnr - antspymm/processing/qc.py
- [x] dvars - antspymm/processing/qc.py
- [x] mask_snr - antspymm/processing/qc.py
- [x] slice_snr - antspymm/processing/qc.py
- [x] foreground_background_snr - antspymm/processing/qc.py
- [x] quantile_snr - antspymm/processing/qc.py
- [x] bvec_reorientation - antspymm/processing/dti.py
- [x] get_dti - antspymm/processing/dti.py
- [x] deformation_gradient_optimized - antspymm/processing/transforms.py
- [x] segment_timeseries_by_bvalue - antspymm/processing/segmentation.py
- [x] segment_timeseries_by_meanvalue - antspymm/processing/segmentation.py

### Total Functions Extracted: 34

### Next Phase: Core Pipeline Functions
These are the most complex functions with heavy dependencies:
- mm() - Main processing pipeline
- mm_csv() - CSV-based processing
- mm_nrg() - NRG-based processing
