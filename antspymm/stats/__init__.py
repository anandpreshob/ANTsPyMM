"""Stats module for ANTsPyMM"""

from .stats import (
    despike_time_series_afni,
    despike_time_series,
    spec_taper,
    spec_ci,
    spec_pgram,
    alffmap,
)

__all__ = [
    "despike_time_series_afni",
    "despike_time_series",
    "spec_taper",
    "spec_ci",
    "spec_pgram",
    "alffmap",
]
