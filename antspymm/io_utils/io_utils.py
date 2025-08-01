"""
Io Utils functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import numpy as np
import pandas as pd

try:
    import ants
except ImportError:
    ants = None


# read_ants_transforms_to_numpy - 20 lines
def read_ants_transforms_to_numpy(transform_files ):
    """
    Read a list of ANTs transform files and convert them to a NumPy array.
    The function filters out any files that are not .mat and will only  use
    the first .mat in each entry of the list.

    :param transform_files: List of lists of file paths to ANTs transform files.  
    :return: NumPy array of the transforms.
    """
    extension = '.mat'
    # Filter the list of lists
    filtered_lists = [[string for string in sublist if string.endswith(extension)] 
                    for sublist in transform_files]
    transforms = []
    for file in filtered_lists:
        transform = ants.read_transform(file[0])
        np_transform = np.array(ants.get_ants_transform_parameters(transform)[0:9])
        transforms.append(np_transform)
    return np.array(transforms)



# threaded_bind_wide_mm_csvs - 28 lines
def threaded_bind_wide_mm_csvs( mm_wide_csvs, n_workers ):
    from concurrent.futures import as_completed
    from concurrent import futures
    import concurrent.futures
    def chunks(l, n):
        """Yield n number of sequential chunks from l."""
        d, r = divmod(len(l), n)
        for i in range(n):
            si = (d+1)*(i if i < r else r) + d*(0 if i < r else i - r)
            yield l[si:si+(d+1 if i < r else d)]
    import numpy as np
    newx = list( chunks( mm_wide_csvs, n_workers ) )
    import pandas as pd
    alldf = pd.DataFrame()
    alldfavg = pd.DataFrame()
    with futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        to_do = []
        for group in range(len(newx)) :
            future = executor.submit(bind_wide_mm_csvs, newx[group] )
            to_do.append(future)
        results = []
        for future in futures.as_completed(to_do):
            res0, res1 = future.result()
            alldf=pd.concat(  [alldf, res0 ], axis=0, ignore_index=False )
            alldfavg=pd.concat(  [alldfavg, res1 ], axis=0, ignore_index=False )
    return alldf, alldfavg



