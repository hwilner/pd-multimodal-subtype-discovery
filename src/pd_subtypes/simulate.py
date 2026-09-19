"""Synthetic multimodal multi-cohort PD-like data generator.

Generates synthetic data with:
- multiple modalities ("views"): clinical, imaging, DaTscan, CSF;
- planted disease subtypes, each with a biomarker progression sequence
  (SuStaIn-style event ordering);
- subject disease stages sampled along the sequence;
- per-cohort batch (location/scale) shifts.

Used for method development and unit tests before real AMP-PD access.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

VIEWS = ("clinical", "imaging", "datscan", "csf")


@dataclass
class SyntheticDataset:
    """Container for a synthetic multi-cohort multimodal dataset."""

    views: dict[str, pd.DataFrame]  # view name -> feature matrix (subjects x features)
    cohort: pd.Series
    subtype: pd.Series  # planted subtype labels
    stage: pd.Series  # planted disease stage
    sequences: dict[int, np.ndarray]  # subtype -> biomarker event ordering

    @property
    def features(self) -> pd.DataFrame:
        """Concatenated feature matrix across all views."""
        return pd.concat(self.views.values(), axis=1)


def simulate_dataset(
    n_per_cohort: int = 60,
    cohorts: tuple[str, ...] = ("PPMI", "PDBP", "BioFIND"),
    n_subtypes: int = 2,
    features_per_view: dict[str, int] | None = None,
    n_stages: int = 6,
    signal: float = 1.5,
    noise: float = 1.0,
    batch_shift: float = 1.0,
    random_state: int = 0,
) -> SyntheticDataset:
    """Simulate a multimodal multi-cohort PD-like dataset.

    Parameters
    ----------
    n_per_cohort:
        Subjects per cohort.
    cohorts:
        Cohort names.
    n_subtypes:
        Number of planted subtypes.
    features_per_view:
        Number of features per modality; defaults to a small balanced set.
    n_stages:
        Number of disease stages.
    signal:
        Effect size of an "abnormal" biomarker (in SD units).
    noise:
        Observation noise SD.
    batch_shift:
        SD of the per-cohort location shift added to each feature.
    random_state:
        Seed for reproducibility.
    """
    rng = np.random.default_rng(random_state)
    if features_per_view is None:
        features_per_view = {v: 5 for v in VIEWS}

    view_names = list(features_per_view)
    n_features = sum(features_per_view.values())

    # Planted subtype event sequences over the concatenated biomarkers.
    # Each subtype's sequence begins with a distinct block of biomarkers
    # (its "early-affected" signature), giving separable subtype profiles
    # while retaining a meaningful progression ordering.
    feature_groups = np.array_split(np.arange(n_features), n_subtypes)
    sequences = {}
    for s in range(n_subtypes):
        early = rng.permutation(feature_groups[s])
        late_parts = [feature_groups[t] for t in range(n_subtypes) if t != s]
        late = rng.permutation(np.concatenate(late_parts)) if late_parts else np.array([], dtype=int)
        sequences[s] = np.concatenate([early, late])
    # Stable subtype signature vectors (indicator over early groups).
    subtype_signature = {}
    for s in range(n_subtypes):
        sig = np.zeros(n_features)
        sig[feature_groups[s]] = 1.0
        subtype_signature[s] = sig

    rows_views: dict[str, list] = {v: [] for v in view_names}
    cohort_idx, subtype_idx, stage_idx = [], [], []
    subject_ids = []

    # Per-cohort location shifts per feature.
    shifts = {
        c: rng.normal(0.0, batch_shift, size=n_features) for c in cohorts
    }

    for c in cohorts:
        for i in range(n_per_cohort):
            s = int(rng.integers(0, n_subtypes))
            k = int(rng.integers(1, n_stages + 1))
            seq = sequences[s]
            pos = np.empty(n_features)
            pos[seq] = np.arange(n_features)
            scaled_pos = pos / (n_features - 1) * (n_stages - 1)
            abnormal = scaled_pos < k
            x = np.where(abnormal, signal, 0.0)
            # Stable subtype signature: the subtype's early-affected
            # biomarker group is mildly elevated regardless of stage.
            x += subtype_signature[s] * (0.5 * signal)
            x += rng.normal(0.0, noise, size=n_features)
            x += shifts[c]
            offset = 0
            for v in view_names:
                nf = features_per_view[v]
                rows_views[v].append(x[offset : offset + nf])
                offset += nf
            cohort_idx.append(c)
            subtype_idx.append(s)
            stage_idx.append(k)
            subject_ids.append(f"{c}-{i:03d}")

    views = {
        v: pd.DataFrame(
            rows_views[v],
            index=subject_ids,
            columns=[f"{v}_f{j}" for j in range(features_per_view[v])],
        )
        for v in view_names
    }
    return SyntheticDataset(
        views=views,
        cohort=pd.Series(cohort_idx, index=subject_ids, name="cohort"),
        subtype=pd.Series(subtype_idx, index=subject_ids, name="subtype"),
        stage=pd.Series(stage_idx, index=subject_ids, name="stage"),
        sequences=sequences,
    )
