"""Tests for pd_subtypes.amppd staging utilities (no real AMP-PD data needed)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from pd_subtypes import amppd, harmonize
from pd_subtypes.sustain import SuStaInModel


def test_missing_export_raises_with_access_pointer(tmp_path):
    with pytest.raises(amppd.AMPPDDataNotFoundError) as excinfo:
        amppd.load_terra_export(tmp_path / "empty")
    assert "docs/DATA_ACCESS.md" in str(excinfo.value)


@pytest.fixture(scope="module")
def semi_synthetic():
    return amppd.simulate_semi_synthetic(n_per_cohort=40, random_state=0)


def test_semi_synthetic_structure(semi_synthetic):
    ds = semi_synthetic
    assert len(ds.cohort) == 120
    assert set(ds.views) == set(amppd.VIEWS)
    assert "mds_updrs3" in ds.views["clinical"].columns
    assert len(ds.sequences) == 2


def test_terra_export_roundtrip(semi_synthetic, tmp_path):
    amppd.write_terra_export(semi_synthetic, tmp_path)
    views = amppd.load_terra_export(tmp_path)
    matrices, cohort = amppd.build_feature_matrices(views)
    assert len(cohort) == 120
    for name, X in matrices.items():
        assert X.shape[0] == 120
        assert not X.isna().any().any()
    # Values survive the round-trip.
    np.testing.assert_allclose(
        matrices["clinical"].to_numpy(),
        semi_synthetic.views["clinical"].to_numpy(),
        atol=1e-8,
    )
    qc = amppd.integrity_check(views)
    assert len(qc) == 3 * len(amppd.VIEWS)
    assert (qc["n_subjects"] == 40).all()


def test_end_to_end_on_semi_synthetic(semi_synthetic, tmp_path):
    """Full staged pipeline recovers the planted subtypes."""
    amppd.write_terra_export(semi_synthetic, tmp_path)
    views = amppd.load_terra_export(tmp_path)
    matrices, cohort = amppd.build_feature_matrices(views)
    harmonized = {n: harmonize.harmonize(X, cohort) for n, X in matrices.items()}
    X = pd.concat(harmonized.values(), axis=1)
    model = SuStaInModel(n_subtypes=2, n_init=6, random_state=0).fit(X)
    ari = adjusted_rand_score(semi_synthetic.subtype, model.subtype_labels_)
    assert ari > 0.6, f"ARI {ari:.3f} below threshold"
