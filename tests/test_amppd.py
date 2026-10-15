"""Tests for pd_subtypes.amppd staging utilities (no real AMP-PD data needed)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from pd_subtypes import amppd, harmonize
from pd_subtypes.sustain import SuStaInModel


def test_missing_export_raises_with_access_pointer(tmp_path):
    """Test missing export raises with access pointer.

    Args:
        tmp_path: tmp path.
    """
    with pytest.raises(amppd.AMPPDDataNotFoundError) as excinfo:
        amppd.load_terra_export(tmp_path / "empty")
    assert "docs/DATA_ACCESS.md" in str(excinfo.value)


@pytest.fixture(scope="module")
def semi_synthetic():
    """Semi synthetic.

    Returns:
        The synthetic.
    """
    return amppd.simulate_semi_synthetic(n_per_cohort=40, random_state=0)


def test_semi_synthetic_structure(semi_synthetic):
    """Test semi synthetic structure.

    Args:
        semi_synthetic: semi synthetic.
    """
    ds = semi_synthetic
    assert len(ds.cohort) == 120
    assert set(ds.views) == set(amppd.VIEWS)
    assert "mds_updrs3" in ds.views["clinical"].columns
    assert len(ds.sequences) == 2


def test_terra_export_roundtrip(semi_synthetic, tmp_path):
    """Test terra export roundtrip.

    Args:
        semi_synthetic: semi synthetic.
        tmp_path: tmp path.
    """
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
    # Subject IDs survive the round-trip too: they are the join key across
    # views and the link back to the published AMP-PD manifest.
    assert list(matrices["clinical"].index) == list(
        semi_synthetic.views["clinical"].index
    )
    qc = amppd.integrity_check(views)
    assert len(qc) == 3 * len(amppd.VIEWS)
    assert (qc["n_subjects"] == 40).all()


def _write_export(export_dir, coverage, n_per_cohort=40):
    """Write a Terra-export directory with per-cohort view coverage.

    Args:
        export_dir: Directory to write the TSV exports into.
        coverage: Mapping of cohort name to the views that cohort exports.
        n_per_cohort: Number of synthetic subjects per cohort.

    Returns:
        The set of subject IDs actually staged across all exports.
    """
    staged = set()
    for cohort, views in coverage.items():
        for view in views:
            # Terra exports carry bare subject IDs; load_terra_export adds the
            # cohort prefix, so the staged IDs are <cohort>-<bare id>.
            bare = [f"{i:04d}" for i in range(n_per_cohort)]
            staged.update(f"{cohort}-{b}" for b in bare)
            df = pd.DataFrame(
                np.arange(n_per_cohort * 2, dtype=float).reshape(n_per_cohort, 2),
                index=bare,
                columns=["f_a", "f_b"],
            )
            df.insert(0, "subject_id", df.index)
            df.to_csv(export_dir / f"{cohort}_{view}.tsv", sep="\t", index=False)
    return staged


def test_cohort_labels_cover_every_staged_subject(tmp_path):
    """Cohort labels must survive a cohort that is missing one view.

    A cohort is a property of the subject, not of the view it was
    exported in, so labelling from a single view would drop the whole
    cohort and hide the gap from both the QC report and the caller.
    """
    coverage = {
        "PPMI": amppd.VIEWS,
        # No clinical export for BioFIND, as happens in real AMP-PD staging.
        "BioFIND": ("imaging", "datscan", "csf"),
    }
    staged = _write_export(tmp_path, coverage)
    views = amppd.load_terra_export(tmp_path)
    cohort = views["cohort"]
    assert set(cohort.index) == staged
    assert set(cohort.unique()) == {"PPMI", "BioFIND"}
    # The gap must be visible as zero-subject rows, not as absent rows.
    qc = amppd.integrity_check(views)
    assert set(qc["cohort"]) == {"PPMI", "BioFIND"}
    missing = qc[
        (qc["cohort"] == "BioFIND") & (qc["view"] == "clinical")
    ]
    assert len(missing) == 1
    assert int(missing["n_subjects"].iloc[0]) == 0


def test_incomplete_cohort_is_reported_not_dropped_silently(tmp_path):
    """A cohort lost to incomplete view coverage must raise a warning."""
    coverage = {
        "PPMI": amppd.VIEWS,
        "BioFIND": ("imaging", "datscan", "csf"),
    }
    _write_export(tmp_path, coverage)
    views = amppd.load_terra_export(tmp_path)
    with pytest.warns(UserWarning, match="incomplete view coverage"):
        matrices, cohort = amppd.build_feature_matrices(views)
    # PPMI has every view, so it survives; BioFIND legitimately cannot.
    assert set(cohort.unique()) == {"PPMI"}
    assert len(cohort) == 40
    assert all(X.shape[0] == 40 for X in matrices.values())


def test_duplicate_subject_id_in_export_is_rejected(tmp_path):
    """A repeated subject_id must fail loudly instead of duplicating rows."""
    _write_export(tmp_path, {"PPMI": ("clinical",)})
    path = tmp_path / "PPMI_clinical.tsv"
    df = pd.read_csv(path, sep="\t")
    pd.concat([df, df.iloc[[0]]]).to_csv(path, sep="\t", index=False)
    with pytest.raises(ValueError, match="duplicate subject_id"):
        amppd.load_terra_export(tmp_path)


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
