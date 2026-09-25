"""Cross-cohort reproducibility of subtype assignments.

Trains a subtype assignment model in one cohort (nearest subtype
centroid classifier) and assigns subjects in another cohort, with
agreement metrics for reproducibility audits.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score


class SubtypeAssignmentModel:
    """Nearest-centroid subtype assignment model.

    Fit on one cohort's subtype assignments; applied to held-out cohorts
    to test cross-cohort reproducibility.
    """

    def __init__(self) -> None:
        """Initialize the instance."""
        self.centroids_: pd.DataFrame | None = None

    def fit(self, features: pd.DataFrame, labels: np.ndarray) -> "SubtypeAssignmentModel":
        """Estimate subtype centroids (mean signature) in the training cohort."""
        df = features.copy()
        df["_label"] = np.asarray(labels)
        self.centroids_ = df.groupby("_label").mean()
        return self

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Assign each subject to the nearest subtype centroid (correlation distance on subtype signatures)."""
        if self.centroids_ is None:
            raise RuntimeError("Model not fitted.")
        X = features[self.centroids_.columns].to_numpy(dtype=float)
        C = self.centroids_.to_numpy(dtype=float)
        d = _correlation_distance(X, C)
        return self.centroids_.index.to_numpy()[d.argmin(axis=1)]

    def predict_proba(self, features: pd.DataFrame) -> pd.DataFrame:
        """Soft assignments: softmax over negative correlation distances."""
        if self.centroids_ is None:
            raise RuntimeError("Model not fitted.")
        X = features[self.centroids_.columns].to_numpy(dtype=float)
        C = self.centroids_.to_numpy(dtype=float)
        logits = -_correlation_distance(X, C)
        logits -= logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        p /= p.sum(axis=1, keepdims=True)
        return pd.DataFrame(p, index=features.index, columns=self.centroids_.index)


def _correlation_distance(X: np.ndarray, C: np.ndarray) -> np.ndarray:
    Xc = X - X.mean(axis=1, keepdims=True)
    Cc = C - C.mean(axis=1, keepdims=True)
    num = Xc @ Cc.T
    denom = np.linalg.norm(Xc, axis=1)[:, None] * np.linalg.norm(Cc, axis=1)[None, :]
    return 1.0 - num / (denom + 1e-12)


def assignment_agreement(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """Adjusted Rand index between reference and transferred assignments."""
    return float(adjusted_rand_score(labels_true, labels_pred))


def subtype_signature_correlation(
    model: SubtypeAssignmentModel, features: pd.DataFrame, labels: np.ndarray
) -> pd.Series:
    """Correlation between training-cohort subtype signatures and the signatures estimated in a held-out cohort (replication metric).

    Labels are matched by maximum signature correlation.
    """
    ref = model.centroids_
    df = features.copy()
    df["_label"] = np.asarray(labels)
    held = df.groupby("_label").mean()[ref.columns]
    out = {}
    used = set()
    for s in ref.index:
        best, best_lab = -np.inf, None
        for h in held.index:
            if h in used:
                continue
            r = float(np.corrcoef(ref.loc[s], held.loc[h])[0, 1])
            if r > best:
                best, best_lab = r, h
        used.add(best_lab)
        out[s] = best
    return pd.Series(out, name="signature_correlation")
