"""
String manipulation utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os


def nrg_filename_to_subjectvisit(s, separator='-'):
    """
    Extracts a pattern from the input string.
    
    Parameters:
    - s: The input string from which to extract the pattern.
    - separator: The separator used in the string (default is '-').
    
    Returns:
    - A string in the format of 'PREFIX-Number-Date'
    """
    parts = os.path.basename(s).split(separator)
    # Assuming the pattern is always in the form of PREFIX-Number-Date-...
    # and PREFIX is always "PPMI", extract the first three parts
    extracted = separator.join(parts[:3])
    return extracted


def parse_nrg_filename( x, separator='-' ):
    """
    split a NRG filename into its named parts
    """
    temp = x.split( separator )
    if len(temp) != 5:
        raise ValueError(x + " not a valid NRG filename")
    return {
        'project':temp[0],
        'subjectID':temp[1],
        'date':temp[2],
        'modality':temp[3],
        'imageID':temp[4]
    }


def validate_filename(filename, valid_keywords, error_message):
    """
    Validates if the filename contains at least one of the valid keywords.
    
    Parameters:
    filename (str): The filename to validate.
    valid_keywords (list): A list of valid keywords that should be in the filename.
    error_message (str): The error message to raise if validation fails.
    
    Raises:
    ValueError: If the filename does not contain any of the valid keywords.
    """
    if not any(keyword in filename for keyword in valid_keywords):
        raise ValueError(f"{error_message}: {filename}")


def validate_modality(modality, valid_modalities):
    """
    Validates if the modality is in the list of valid modalities.
    """
    if modality not in valid_modalities:
        raise ValueError(f"Invalid modality '{modality}'. Must be one of {valid_modalities}")


def nrg_format_path( projectID, subjectID, date, modality, imageID, separator='-' ):
    """
    Generate a path name in NRG format

    Example:

    import antspymm
    ppmi="PPMI"
    sid="3000"
    dt="20140205"
    mid="T1w"
    iid="000"
    pth = antspymm.nrg_format_path( ppmi, sid, dt, mid, iid )
    print(pth)

    Arguments
    ---------
    projectID : string

    subjectID : string

    date : string

    modality : string

    imageID : string

    separator : string default -

    Returns
    -------
    String

    """
    thedirectory = os.path.join( str(projectID), str(subjectID), str(date), str(modality), str(imageID) )
    thefilename = str(projectID) + separator + str(subjectID) + separator + str(date) + separator + str(modality) + separator + str(imageID)
    return os.path.join( thedirectory, thefilename )