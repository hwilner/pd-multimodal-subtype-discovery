"""Tests for the Paper 1 semi-synthetic results package (reports/paper1/).

Covers issue #15's demo track: the table/figure scripts must regenerate
their committed outputs byte-identically, every rendered number must match
the committed artifacts, and the numbers quoted in docs/RESULTS.md must not
drift from the artifacts. No benchmark quantity is re-measured here; these
tests guard integrity and determinism only.
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER1 = REPO_ROOT / "reports" / "paper1"
REPORTS = REPO_ROOT / "reports"
TABLES_MD = PAPER1 / "tables_1_to_3_semisynthetic.md"
FIGURE_SVG = PAPER1 / "figure2_cross_cohort_demo.svg"

sys.path.insert(0, str(PAPER1))
import make_figures  # noqa: E402
import make_tables  # noqa: E402


@pytest.fixture(scope="module")
def artifacts():
    """Load the three committed semi-synthetic artifacts.

    Returns:
        Tuple of (QC frame, subtype-counts frame, summary dict).
    """
    return make_tables.load_artifacts(REPORTS)


def test_committed_artifacts_are_internally_consistent(artifacts):
    """Committed QC/counts/summary artifacts must agree with each other.

    Args:
        artifacts: Fixture of committed artifacts.
    """
    qc, counts, summary = artifacts
    assert make_tables.check_consistency(qc, counts, summary) == []


def test_make_tables_refuses_inconsistent_artifacts(artifacts, tmp_path):
    """The renderer must refuse to write when artifacts disagree.

    Args:
        artifacts: Fixture of committed artifacts.
        tmp_path: Pytest temporary directory.
    """
    qc, counts, summary = artifacts
    bad_summary = dict(summary, n_subjects=summary["n_subjects"] + 1)
    problems = make_tables.check_consistency(qc, counts, bad_summary)
    assert any("n_subjects" in p for p in problems)


def test_tables_regenerate_byte_identical(tmp_path):
    """Re-running make_tables.py must reproduce the committed file exactly.

    Args:
        tmp_path: Pytest temporary directory.
    """
    out = tmp_path / "tables.md"
    subprocess.run(
        [sys.executable, str(PAPER1 / "make_tables.py"), "--out", str(out)],
        check=True, capture_output=True,
    )
    assert out.read_bytes() == TABLES_MD.read_bytes()


def test_figure_regenerates_byte_identical(tmp_path):
    """Re-running make_figures.py must reproduce the committed SVG exactly.

    Args:
        tmp_path: Pytest temporary directory.
    """
    out = tmp_path / "figure.svg"
    subprocess.run(
        [sys.executable, str(PAPER1 / "make_figures.py"), "--out", str(out)],
        check=True, capture_output=True,
    )
    assert out.read_bytes() == FIGURE_SVG.read_bytes()


def test_figure_is_deterministic_across_hash_seeds(tmp_path):
    """SVG output must not depend on PYTHONHASHSEED.

    Args:
        tmp_path: Pytest temporary directory.
    """
    outs = []
    for i, seed in enumerate(("0", "42")):
        out = tmp_path / f"figure_{i}.svg"
        subprocess.run(
            [sys.executable, str(PAPER1 / "make_figures.py"), "--out", str(out)],
            check=True, capture_output=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
        )
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]


def test_rendered_table_values_match_artifacts(artifacts):
    """Every numeric cell in the rendered tables must match the artifacts.

    Args:
        artifacts: Fixture of committed artifacts.
    """
    qc, counts, summary = artifacts
    text = make_tables.render_tables(qc, counts, summary)
    assert f"| Subjects / features | {summary['n_subjects']} / {summary['n_features']} |" in text
    assert f"| SuStaIn log-likelihood | −{abs(summary['sustain_log_likelihood']):.2f} |" in text
    assert f"| SuStaIn vs. multi-view consensus ARI | {summary['sustain_vs_consensus_ari']:.3f} |" in text
    for cohort, metrics in summary["cross_cohort"].items():
        assert (
            f"| {summary['train_cohort']} → {cohort} assignment ARI "
            f"| {metrics['assignment_ari']:.3f} |"
        ) in text
        assert (
            f"| {summary['train_cohort']} → {cohort} subtype-signature correlation "
            f"| {metrics['signature_correlation']:.3f} |"
        ) in text
    totals_row = (
        f"| **Total** | **{qc['view'].nunique()} views** "
        f"| **{int(qc.groupby('cohort')['n_subjects'].first().sum())}** "
        f"| **{int(qc.groupby('cohort')['n_features'].sum().iloc[0])}** "
    )
    assert totals_row in text


def test_results_doc_tables_match_artifacts():
    """Doc-drift guard: docs/RESULTS.md Tables 1-3 must quote the artifacts.

    Every metric row line of the rendered Table 3 and every data row of the
    rendered Tables 1-2 must appear verbatim in docs/RESULTS.md.
    """
    doc = (REPO_ROOT / "docs" / "RESULTS.md").read_text()
    rendered = TABLES_MD.read_text()
    table_lines = [
        line for line in rendered.splitlines()
        if line.startswith("| ") and not set(line) <= set("|-: ")
        and "Cohort |" not in line and "Metric |" not in line
    ]
    assert len(table_lines) >= 20  # 12 QC rows + total + 3 counts + 8 metrics
    missing = [line for line in table_lines if line not in doc]
    assert not missing, f"docs/RESULTS.md drifted from artifacts: {missing}"


def test_figure_is_well_formed_and_labeled():
    """The SVG must parse as XML and carry the not-real-data disclaimer."""
    root = ET.parse(FIGURE_SVG).getroot()
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    text = FIGURE_SVG.read_text()
    assert "not real participant data" in text
    assert "reports/subtyping_summary.json" in text


def test_figure_bars_match_artifact_values():
    """Every bar label in the SVG must match the committed summary values."""
    with open(REPORTS / "subtyping_summary.json") as fh:
        summary = json.load(fh)
    text = FIGURE_SVG.read_text()
    for metrics in summary["cross_cohort"].values():
        assert f">{metrics['assignment_ari']:.3f}<" in text
        assert f">{metrics['signature_correlation']:.3f}<" in text


def test_qc_report_matches_staged_counts():
    """Sanity check on the QC artifact: 240 subjects, 12 features, no gaps."""
    qc = pd.read_csv(REPORTS / "qc_report_semisynthetic.csv")
    assert qc.groupby("cohort")["n_subjects"].first().sum() == 240
    assert (qc["frac_missing"] == 0).all()
    assert (qc["n_constant_features"] == 0).all()
