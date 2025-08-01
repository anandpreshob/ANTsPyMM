"""Analysis module for ANTsPyMM"""

from .analysis import (
    estimate_optimal_pca_components,
    calculate_trimmed_mean,
    calculate_CBF,
    calculate_loop_scores_full,
    novelty_detection_ee,
    novelty_detection_svm,
    novelty_detection_lof,
    novelty_detection_loop,
    novelty_detection_quantile,
)

__all__ = [
    "estimate_optimal_pca_components",
    "calculate_trimmed_mean",
    "calculate_CBF",
    "calculate_loop_scores_full",
    "novelty_detection_ee",
    "novelty_detection_svm",
    "novelty_detection_lof",
    "novelty_detection_loop",
    "novelty_detection_quantile",
]
