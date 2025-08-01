"""
Version utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""


def version( ):
    """
    report versions of this package and primary dependencies

    Arguments
    ---------
    None

    Returns
    -------
    a dictionary with package name and versions

    Example
    -------
    >>> import antspymm
    >>> antspymm.version()
    """
    import pkg_resources
    return {
              'tensorflow': pkg_resources.get_distribution("tensorflow").version,
              'antspyx': pkg_resources.get_distribution("antspyx").version,
              'antspynet': pkg_resources.get_distribution("antspynet").version,
              'antspyt1w': pkg_resources.get_distribution("antspyt1w").version,
              'antspymm': pkg_resources.get_distribution("antspymm").version
              }