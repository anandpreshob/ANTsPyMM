"""
Data manipulation utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np
import pandas as pd

# Import ants only when needed
try:
    import ants
except ImportError:
    ants = None


def extend_list_to_length(lst, target_length, fill_value=None):
    return lst + [fill_value] * (target_length - len(lst))


def get_antsimage_keys(dictionary):
    """
    Return the keys of the dictionary where the values are ANTsImages.

    :param dictionary: A dictionary to inspect
    :return: A list of keys for which the values are ANTsImages
    """
    if ants is None:
        raise ImportError("ants package is required for get_antsimage_keys function")
    return [key for key, value in dictionary.items() if isinstance(value, ants.core.ants_image.ANTsImage)]


def get_first_item_as_string(df, column_name):
    """
    Check if the first item in the specified column of the DataFrame is a string.
    If it is not a string, attempt to convert it to an integer and then to a string.

    Parameters:
    df (pd.DataFrame): The DataFrame to operate on.
    column_name (str): The name of the column to check.

    Returns:
    str: The first item in the specified column, guaranteed to be returned as a string.
    """
    if isinstance(df[column_name].iloc[0], str):
        return df[column_name].iloc[0]
    else:
        try:
            return str(int(df[column_name].iloc[0]))
        except ValueError:
            raise ValueError("The value cannot be converted to an integer.")


def convert_np_in_dict(data_dict):
    """
    Convert values in the dictionary from nupmy float or int to regular float or int.

    :param data_dict: A dictionary with values of various types.
    :return: Dictionary with numpy values converted.
    """
    converted_dict = {}
    for key, value in data_dict.items():
        if isinstance(value, (np.float32, np.float64)):
            converted_dict[key] = float(value)
        elif isinstance(value, (np.int8,  np.uint8, np.int16,  np.uint16, np.int32,  np.uint32, np.int64,  np.uint64)):
            converted_dict[key] = int(value)
        else:
            converted_dict[key] = value
    return converted_dict