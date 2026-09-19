"""Unit tests for pd_subtypes on synthetic data (no real AMP-PD data needed)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from pd_subtypes import harmonize, multiview, reproducibility, simulate
from pd_subtypes.sustain import SuStaInModel


@pytest.fixture(scope="module")
def dataset():
    return simulate.simulate_dataset(
        n_per_cohort=60, n_subtypes=2, signal=2.0, noise=0.8,
        batch_shift=1.5, random_state=42,
    )


@pytest.fixture(scope="module")
def harmonized(dataset):
    out = {}
    for name, view in dataset.views.items():
        out[name] = harmonize.harmonize(view, dataset.cohort)
    return out


def test_harmonization_removes_planted_cohort_shifts(dataset, harmonized):
    for name, view in dataset.views.items():
        before = harmonize.cohort_shift_magnitude(view, dataset.cohort).mean()
        after = harmonize.cohort_shift_magnitude(harmonized[name], dataset.cohort).mean()
        assert after < 0.2 * before, f"{name}: shift {before:.3f} -> {after:.3f}"


def test_zscore_within_cohort(dataset):
    view = dataset.views["clinical"]
    z = harmonize.zscore_within_cohort(view, dataset.cohort)
    for c in dataset.cohort.unique():
        block = z[dataset.cohort == c]
        assert np.allclose(block.mean(), 0, atol=1e-8)
        assert np.allclose(block.std(ddof=0), 1, atol=1e-6)


def test_sustain_recovers_planted_subtypes(dataset, harmonized):
    X = pd.concat(harmonized.values(), axis=1)
    model = SuStaInModel(n_subtypes=2, n_init=6, random_state=0).fit(X)
    ari = adjusted_rand_score(dataset.subtype, model.subtype_labels_)
    assert ari > 0.6, f"ARI {ari:.3f} below threshold"


def test_multiview_consensus_recovers_structure(dataset, harmonized):
    labels = multiview.consensus_clustering(harmonized, n_clusters=2)
    ari = adjusted_rand_score(dataset.subtype, labels)
    assert ari > 0.4, f"consensus ARI {ari:.3f} below threshold"


def test_assignment_model_transfers_across_cohorts(dataset, harmonized):
    X = pd.concat(harmonized.values(), axis=1)
    cohorts = dataset.cohort.unique()
    train_c, test_c = cohorts[0], cohorts[1]
    train_mask = dataset.cohort == train_c
    test_mask = dataset.cohort == test_c
    model = reproducibility.SubtypeAssignmentModel().fit(
        X[train_mask], dataset.subtype[train_mask].to_numpy()
    )
    pred = model.predict(X[test_mask])
    ari = reproducibility.assignment_agreement(
        dataset.subtype[test_mask].to_numpy(), pred
    )
    assert ari > 0.6, f"cross-cohort ARI {ari:.3f} below threshold"
    corr = reproducibility.subtype_signature_correlation(
        model, X[test_mask], dataset.subtype[test_mask].to_numpy()
    )
    assert corr.mean() > 0.8, f"signature replication {corr.mean():.3f}"


def test_simulation_shapes(dataset):
    assert len(dataset.cohort) == 180
    assert set(dataset.views) == {"clinical", "imaging", "datscan", "csf"}
    assert dataset.features.shape[1] == 20
