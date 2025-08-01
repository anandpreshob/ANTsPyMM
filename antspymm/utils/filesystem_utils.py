"""
File system utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import re
import warnings
import subprocess
from datetime import datetime, timedelta


def validate_nrg_file_format(path, separator):
    """
    is your path nrg-etic?
    Validates if a given path conforms to the NRG file format, taking into account known extensions
    and the expected directory structure.

    :param path: The file path to validate.
    :param separator: The separator used in the filename and directory structure.
    :return: A tuple (bool, str) indicating whether the path is valid and a message explaining the validation result.

    : example

    ntfn='/Users/ntustison/Data/Stone/LIMBIC/NRG/ANTsLIMBIC/sub08C105120Yr/ses-1/rsfMRI_RL/000/ANTsLIMBIC_sub08C105120Yr_ses-1_rsfMRI_RL_000.nii.gz'
    ntfngood='/Users/ntustison/Data/Stone/LIMBIC/NRG/ANTsLIMBIC/sub08C105120Yr/ses_1/rsfMRI_RL/000/ANTsLIMBIC-sub08C105120Yr-ses_1-rsfMRI_RL-000.nii.gz'

    validate_nrg_detailed(ntfngood, '-')
    print( validate_nrg_detailed(ntfn, '-') )
    print( validate_nrg_detailed(ntfn, '_') )

    """
    import re    

    def normalize_path(path):
        """
        Replace multiple repeated '/' with just a single '/'
        
        :param path: The file path to normalize.
        :return: The normalized file path with single '/'.
        """
        normalized_path = re.sub(r'/+', '/', path)
        return normalized_path

    def strip_known_extension(filename, known_extensions):
        """
        Strips a known extension from the filename.

        :param filename: The filename from which to strip the extension.
        :param known_extensions: A list of known extensions to strip from the filename.
        :return: The filename with the known extension stripped off, if found.
        """
        for ext in known_extensions:
            if filename.endswith(ext):
                # Strip the extension and return the modified filename
                return filename[:-len(ext)]
        # If no known extension is found, return the original filename
        return filename

    import warnings
    if normalize_path( path ) != path:
        path = normalize_path( path )
        warnings.warn("Probably had multiple repeated slashes eg /// in the file path.  this might cause issues. clean up with re.sub(r'/+', '/', path)")

    known_extensions = [".nii.gz", ".nii", ".mhd", ".nrrd", ".mha", ".json", ".bval", ".bvec"]
    known_extensions2 = [ext.lstrip('.') for ext in known_extensions]
    def get_extension(filename, known_extensions ):
        # List of known extensions in priority order
        for ext in known_extensions:
            if filename.endswith(ext):
                return ext.strip('.')
        return "Invalid extension"
    
    parts = path.split('/')
    if len(parts) < 7:  # Checking for minimum path structure
        return False, "Path structure is incomplete. Expected at least 7 components, found {}.".format(len(parts))
    
    # Extract directory components and filename
    directory_components = parts[1:-1]  # Exclude the root '/' and filename
    filename = parts[-1]
    filename_without_extension = strip_known_extension( filename, known_extensions )
    file_extension = get_extension( filename, known_extensions )
    
    # Validating file extension
    if file_extension not in known_extensions2:
        print( file_extension )
        return False, "Invalid file extension: {}. Expected 'nii.gz' or 'json'.".format(file_extension)
    
    # Splitting the filename to validate individual parts
    filename_parts = filename_without_extension.split(separator)
    if len(filename_parts) != 5:  # Expecting 5 parts based on the NRG format
        print( filename_parts )
        return False, "Filename does not have exactly 5 parts separated by '{}'. Found {} parts.".format(separator, len(filename_parts))
    
    # Reconstruct expected filename from directory components
    expected_filename_parts = directory_components[-5:]
    expected_filename = separator.join(expected_filename_parts)
    if filename_without_extension != expected_filename:
        print( filename_without_extension )
        print("--- vs expected ---")
        print( expected_filename )
        return False, "Filename structure does not match directory structure. Expected filename: {}.".format(expected_filename)
    
    # Validate directory structure against NRG format
    study_name, subject_id, session, modality = directory_components[-4:-1] + [directory_components[-1].split('/')[0]]
    if not all([study_name, subject_id, session, modality]):
        return False, "Directory structure does not follow NRG format. Ensure StudyName, SubjectID, Session (ses_x), and Modality are correctly specified."
    
    # If all checks pass
    return True, "The path conforms to the NRG format."


def find_most_recent_file(file_list):
    """
    Finds and returns the most recently modified file from a list of file paths.
    
    Parameters:
    - file_list: A list of strings, where each string is a path to a file.
    
    Returns:
    - The path to the most recently modified file in the list, or None if the list is empty or contains no valid files.
    """
    # Filter out items that are not files or do not exist
    valid_files = [f for f in file_list if os.path.isfile(f)]
    
    # Check if the filtered list is not empty
    if valid_files:
        # Find the file with the latest modification time
        most_recent_file = max(valid_files, key=os.path.getmtime)
        return [most_recent_file]
    else:
        return None


def clean_tmp_directory(age_hours=1., use_sudo=False, extensions=[ '.nii', '.nii.gz' ], log_file_path=None):
    """
    Clean the /tmp directory by removing files and directories older than a certain number of hours.
    Optionally uses sudo and can filter files by extensions.

    :param age_hours: Age in hours to consider files and directories for deletion.
    :param use_sudo: Whether to use sudo for removal commands.
    :param extensions: List of file extensions to delete. If None, all files are considered.
    :param log_file_path: Path to the log file. If None, a default path will be used based on the OS.

    # Usage
    # Example: clean_tmp_directory(age_hours=1, use_sudo=True, extensions=['.log', '.tmp'])
    """
    import os
    import platform
    import subprocess
    from datetime import datetime, timedelta

    if not isinstance(age_hours, float):
        return

    # Determine the tmp directory based on the operating system
    tmp_dir = '/tmp'

    # Set the log file path
    if log_file_path is not None:
        log_file = log_file_path

    current_time = datetime.now()
    for item in os.listdir(tmp_dir):
        try:
            item_path = os.path.join(tmp_dir, item)
            item_stat = os.stat(item_path)

            # Calculate the age of the file/directory
            item_age = current_time - datetime.fromtimestamp(item_stat.st_mtime)
            if item_age > timedelta(hours=age_hours):
                # Check for file extensions if provided
                if extensions is None or any(item.endswith(ext) for ext in extensions):
                    # Construct the removal command
                    rm_command = ['sudo', 'rm', '-rf', item_path] if use_sudo else ['rm', '-rf', item_path]
                    subprocess.run(rm_command)

                if log_file_path is not None:
                    with open(log_file, 'a') as log:
                        log.write(f"{datetime.now()}: Deleted {item_path}\n")
        except Exception as e:
            if log_file_path is not None:
                with open(log_file, 'a') as log:
                    log.write(f"{datetime.now()}: Error deleting {item_path}: {e}\n")