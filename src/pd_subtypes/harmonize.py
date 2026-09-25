"""Cross-cohort feature harmonization.

Implements within-cohort z-scoring and a simplified ComBat-style batch
correction (location-and-scale adjustment per cohort per feature) for
multimodal feature matrices (clinical, imaging, DaTscan, CSF).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def zscore_within_cohort(
    features: pd.DataFrame, cohort: pd.Series, eps: float = 1e-8
) -> pd.DataFrame:
    """Z-score each feature within each cohort.

    Parameters
    ----------
    features:
    Rows are subjects, columns are features.
    cohort:
    Cohort label per row, aligned with ``features.index``.
    eps:
    Small constant added to the standard deviation for stability.

    Returns:
    -------
    pd.DataFrame
    Feature matrix with per-cohort mean 0 and std 1 per feature.
    """
    cohort = pd.Series(cohort, index=features.index)
    out = features.copy().astype(float)
    for c in cohort.unique():
        mask = cohort == c
        block = out.loc[mask]
        out.loc[mask] = (block - block.mean()) / (block.std(ddof=0) + eps)
    return out


def combat_batch_correction(
    features: pd.DataFrame,
    cohort: pd.Series,
    covariates: pd.DataFrame | None = None,
    eps: float = 1e-8,
) -> pd.DataFrame:
    """Simplified ComBat-style location/scale batch correction.

    Removes per-cohort additive (location) and multiplicative (scale)
    effects from each feature while optionally preserving variation
    explained by biological covariates (e.g. age, sex, diagnosis).

    Parameters
    ----------
    features:
    Rows are subjects, columns are features.
    cohort:
    Cohort (batch) label per row.
    covariates:
    Optional biological covariates to preserve (one row per subject).
    eps:
    Numerical stability constant.

    Returns:
    -------
    pd.DataFrame
    Batch-corrected feature matrix.
    """
    X = features.to_numpy(dtype=float)
    cohort = pd.Series(cohort, index=features.index).to_numpy()
    n, _ = X.shape

    # Optional biological signal (from covariates) to preserve.
    if covariates is not None:
        B = covariates.to_numpy(dtype=float)
        B = np.column_stack([B, np.ones(n)])
        coef, *_ = np.linalg.lstsq(B, X, rcond=None)
        fitted = B @ coef
    else:
        fitted = np.zeros((n, X.shape[1]))
    resid = X - fitted

    grand_mean = resid.mean(axis=0)
    pooled_std = resid.std(axis=0, ddof=0) + eps

    corrected = np.empty_like(X)
    for c in np.unique(cohort):
        mask = cohort == c
        R = resid[mask]
        loc = R.mean(axis=0)
        scale = R.std(axis=0, ddof=0) + eps
        corrected[mask] = (R - loc) / scale * pooled_std + grand_mean

    corrected += fitted
    return pd.DataFrame(corrected, index=features.index, columns=features.columns)


def harmonize(
    features: pd.DataFrame,
    cohort: pd.Series,
    covariates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Full harmonization pipeline: ComBat-style correction, then global z-score.

    Parameters
    ----------
    features:
    Rows are subjects, columns are features.
    cohort:
    Cohort label per row.
    covariates:
    Optional biological covariates preserved during batch correction.

    Returns:
    -------
    pd.DataFrame
    Harmonized, globally standardized feature matrix.
    """
    corrected = combat_batch_correction(features, cohort, covariates=covariates)
    return (corrected - corrected.mean()) / (corrected.std(ddof=0) + 1e-8)


def cohort_shift_magnitude(features: pd.DataFrame, cohort: pd.Series) -> pd.Series:
    """Diagnostic: per-feature magnitude of the largest inter-cohort mean shift.

    Useful as a batch-effect diagnostic before/after harmonization.
    """
    cohort = pd.Series(cohort, index=features.index)
    global_mean = features.mean()
    shifts = {}
    for col in features.columns:
        cohort_means = features.groupby(cohort)[col].mean()
        shifts[col] = float((cohort_means - global_mean[col]).abs().max())
    return pd.Series(shifts)
