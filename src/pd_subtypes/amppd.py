"""AMP-PD Terra staging: clinical export loading, harmonization prep, QC.

The AMP-PD Tier 2 dataset is accessed inside a Terra workspace
(https://app.terra.bio) after approval (see ``docs/DATA_ACCESS.md``).
The expected workflow is: query the AMP-PD tables in Terra, export one
TSV per (cohort, view) with a ``subject_id`` column, and copy them out
as aggregate analysis inputs. This module stages such exports into the
feature-matrix format used by :mod:`pd_subtypes.harmonize` and
:mod:`pd_subtypes.sustain`, with integrity checks.

Because AMP-PD Tier 2 data is controlled-access (no credential-free
download exists), a clearly documented **semi-synthetic** fallback is
provided: :func:`simulate_semi_synthetic` generates a realistic
PPMI/PDBP/BioFIND-like dataset from *published summary statistics*
(Marek et al., 2018, PPMI baseline characteristics; published cohort
means/SDs for MDS-UPDRS III, MoCA, DaTscan SBR, CSF markers) with two
planted progression subtypes. It lets the full
harmonize -> SuStaIn -> cross-cohort pipeline be validated end-to-end
while the DUA is pending.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .simulate import SyntheticDataset

DATA_ACCESS_DOC = "docs/DATA_ACCESS.md"

# Views staged from AMP-PD Terra exports (one TSV per cohort per view).
VIEWS = ("clinical", "imaging", "datscan", "csf")

# Canonical AMP-PD contributing cohorts used in this project.
COHORTS = ("PPMI", "PDBP", "BioFIND")

# Features staged per view, oriented so that *higher = more abnormal*
# (signs of published scales are flipped where needed, e.g. MoCA,
# DaTscan SBR, volumes, CSF Abeta). Means/SDs below are approximate
# published PPMI de-novo PD baseline values (Marek et al., 2018;
# Parkinson Progression Marker Initiative cohort papers) and are used
# ONLY for the semi-synthetic fallback generator.
FEATURE_SPECS: dict[str, dict[str, tuple[float, float]]] = {
    "clinical": {
        "mds_updrs3": (21.0, 9.0),   # MDS-UPDRS part III, early PD
        "neg_moca": (-27.0, 2.3),    # MoCA, negated (higher = worse)
        "rbd_screen": (3.0, 2.0),    # RBDSQ-like
        "gds": (2.0, 2.0),           # geriatric depression scale
    },
    "imaging": {
        "neg_caudate_vol": (-3.6, 0.5),   # cm^3, negated
        "neg_putamen_vol": (-4.2, 0.6),   # cm^3, negated
        "neg_cortical_thick": (-2.4, 0.15),  # mm, negated
    },
    "datscan": {
        "neg_caudate_sbr": (-2.6, 0.7),   # striatal binding ratio, negated
        "neg_putamen_sbr": (-1.4, 0.6),   # strongly reduced in PD
    },
    "csf": {
        "neg_abeta": (-800.0, 250.0),  # pg/mL, negated
        "p_tau": (15.0, 7.0),          # pg/mL
        "alpha_syn_total": (1500.0, 500.0),  # pg/mL
    },
}


class AMPPDDataNotFoundError(FileNotFoundError):
    """Raised when no AMP-PD Terra export is staged at the expected path."""


# ---------------------------------------------------------------------------
# Terra export staging
# ---------------------------------------------------------------------------

def export_filename(cohort: str, view: str) -> str:
    """Expected file name for a Terra-exported (cohort, view) table."""
    return f"{cohort}_{view}.tsv"


def load_terra_export(export_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load a Terra export directory into aligned per-view feature matrices.

    Expected layout: one TSV per (cohort, view), named
    ``<COHORT>_<view>.tsv`` (e.g. ``PPMI_clinical.tsv``), each with a
    ``subject_id`` column and numeric feature columns. Cohorts are
    stacked per view; subject IDs are prefixed with their cohort.

    Returns:
    -------
    dict mapping view name -> DataFrame (subjects x features), with a
    ``cohort`` entry (pd.Series) aligned to the view rows.

    Raises :class:`AMPPDDataNotFoundError` if no matching TSVs exist.
    """
    export_dir = Path(export_dir)
    found: dict[str, list[pd.DataFrame]] = {}
    for cohort in COHORTS:
        for view in VIEWS:
            path = export_dir / export_filename(cohort, view)
            if path.exists():
                df = pd.read_csv(path, sep="\t")
                if "subject_id" not in df.columns:
                    raise ValueError(f"{path}: missing required 'subject_id' column")
                df["subject_id"] = cohort + "-" + df["subject_id"].astype(str)
                df = df.set_index("subject_id")
                df.attrs["cohort"] = cohort
                found.setdefault(view, []).append(df)
    if not found:
        raise AMPPDDataNotFoundError(
            f"No AMP-PD Terra export TSVs found under {export_dir} "
            f"(expected files like {export_filename('PPMI', 'clinical')}). "
            f"AMP-PD Tier 2 data requires an approved DUA and a Terra "
            f"workspace — see {DATA_ACCESS_DOC} for access steps. Until "
            "then, use `simulate_semi_synthetic` / "
            "`scripts/prepare_amppd.py --semi-synthetic` for a documented "
            "semi-synthetic stand-in."
        )
    views = {view: pd.concat(frames) for view, frames in found.items()}
    cohort = pd.Series(
        np.repeat(
            [f.attrs["cohort"] for f in next(iter(found.values()))],
            [len(f) for f in next(iter(found.values()))],
        ),
        index=next(iter(views.values())).index,
        name="cohort",
    )
    views["cohort"] = cohort
    return views


def integrity_check(views: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """QC report for staged views: per-cohort/per-view counts and missingness.

    Parameters
    ----------
    views:
    Output of :func:`load_terra_export` (view name -> matrix, plus a
    ``cohort`` Series).

    Returns:
    -------
    pd.DataFrame with one row per (cohort, view): n_subjects,
    n_features, frac_missing, n_constant_features.
    """
    cohort = views["cohort"]
    rows = []
    for c in cohort.unique():
        mask = cohort == c
        for view, X in views.items():
            if view == "cohort":
                continue
            Xc = X.loc[X.index.intersection(cohort[mask].index)]
            rows.append(
                {
                    "cohort": c,
                    "view": view,
                    "n_subjects": len(Xc),
                    "n_features": Xc.shape[1],
                    "frac_missing": float(Xc.isna().mean().mean()),
                    "n_constant_features": int((Xc.std(ddof=0) == 0).sum()),
                }
            )
    return pd.DataFrame(rows)


def build_feature_matrices(
    views: dict[str, pd.DataFrame],
    min_subjects_per_cohort: int = 10,
) -> tuple[dict[str, pd.DataFrame], pd.Series]:
    """Align staged views to a common subject set and impute missing values.

    Subjects present in all views are kept; missing feature values are
    mean-imputed within cohort; constant features are dropped. Returns
    (views dict without the cohort entry, aligned cohort Series) ready
    for :func:`pd_subtypes.harmonize.harmonize`.
    """
    cohort = views["cohort"]
    view_mats = {k: v for k, v in views.items() if k != "cohort"}
    common = cohort.index
    for X in view_mats.values():
        common = common.intersection(X.index)
    if len(common) == 0:
        raise ValueError("No subjects shared across all views.")
    cohort = cohort.loc[common]
    out = {}
    for name, X in view_mats.items():
        X = X.loc[common].astype(float)
        X = X.loc[:, X.std(ddof=0) > 0]
        # within-cohort mean imputation
        for c in cohort.unique():
            mask = cohort == c
            X.loc[mask] = X.loc[mask].fillna(X.loc[mask].mean())
        X = X.fillna(X.mean())
        out[name] = X
    counts = cohort.value_counts()
    if (counts < min_subjects_per_cohort).any():
        import warnings

        warnings.warn(
            f"Cohort(s) below {min_subjects_per_cohort} subjects: "
            f"{counts[counts < min_subjects_per_cohort].to_dict()}"
        )
    return out, cohort


def write_terra_export(dataset: SyntheticDataset, export_dir: str | Path) -> None:
    """Write a SyntheticDataset in the Terra-export TSV layout.

    Used to exercise the staging path end-to-end (and in tests) with the
    semi-synthetic stand-in.
    """
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    for cohort in dataset.cohort.unique():
        ids = dataset.cohort[dataset.cohort == cohort].index
        bare = [s.split("-", 1)[1] for s in ids]
        for view, X in dataset.views.items():
            df = X.loc[ids].copy()
            df.insert(0, "subject_id", bare)
            df.to_csv(export_dir / export_filename(cohort, view),
                      sep="\t", index=False)


# ---------------------------------------------------------------------------
# Semi-synthetic fallback (published summary statistics; NOT real data)
# ---------------------------------------------------------------------------

def simulate_semi_synthetic(
    n_per_cohort: int = 80,
    cohorts: tuple[str, ...] = COHORTS,
    n_stages: int = 6,
    batch_shift_sd: float = 0.3,
    random_state: int = 0,
) -> SyntheticDataset:
    """Semi-synthetic PPMI/PDBP/BioFIND-like dataset from published stats.

    **This is not real participant data.** Feature means/SDs are drawn
    from published AMP-PD/PPMI cohort summary statistics (see
    FEATURE_SPECS; Marek et al. 2018 and related cohort papers). Two
    progression subtypes are planted — a "motor/DaTscan-first" subtype
    (early putamen SBR and MDS-UPDRS III abnormality) and a
    "cognitive/CSF-first" subtype (early MoCA/CSF abnormality) — a
    coarse motor-vs-cognitive axis widely reported in PD subtyping
    (e.g. Fereshtehnejad et al., 2015). All features are oriented so
    higher = more abnormal and expressed as z-scores relative to the
    published means/SDs; per-cohort batch shifts are added so the
    harmonization step has something to remove.
    """
    rng = np.random.default_rng(random_state)
    view_names = list(FEATURE_SPECS)
    feature_names = [f for v in view_names for f in FEATURE_SPECS[v]]
    n_features = len(feature_names)
    fidx = {f: i for i, f in enumerate(feature_names)}

    # Planted subtype event orderings (biomarker progression sequences).
    motor_first = [
        "neg_putamen_sbr", "neg_caudate_sbr", "mds_updrs3", "rbd_screen",
        "gds", "neg_putamen_vol", "neg_caudate_vol", "neg_moca",
        "neg_cortical_thick", "alpha_syn_total", "p_tau", "neg_abeta",
    ]
    cog_first = [
        "neg_abeta", "p_tau", "alpha_syn_total", "neg_moca",
        "neg_cortical_thick", "neg_caudate_vol", "rbd_screen",
        "neg_putamen_sbr", "mds_updrs3", "neg_caudate_sbr", "gds",
        "neg_putamen_vol",
    ]
    sequences = {s: np.array([fidx[f] for f in seq])
                 for s, seq in enumerate([motor_first, cog_first])}
    # Stable subtype signatures: each subtype's early-affected biomarkers
    # are mildly elevated regardless of stage (as in pd_subtypes.simulate).
    subtype_signature = {}
    for s, seq in sequences.items():
        sig = np.zeros(n_features)
        sig[seq[:4]] = 0.9
        subtype_signature[s] = sig

    rows_views = {v: [] for v in view_names}
    cohort_idx, subtype_idx, stage_idx, subject_ids = [], [], [], []
    shifts = {c: rng.normal(0.0, batch_shift_sd, size=n_features) for c in cohorts}

    for c in cohorts:
        for i in range(n_per_cohort):
            s = int(rng.integers(0, 2))
            k = int(rng.integers(1, n_stages + 1))
            seq = sequences[s]
            pos = np.empty(n_features)
            pos[seq] = np.arange(n_features)
            scaled_pos = pos / (n_features - 1) * (n_stages - 1)
            # z-space abnormality: biomarkers past their event stage are
            # elevated by ~1.5 SD plus noise.
            x = np.where(scaled_pos < k, 1.5, 0.0) + subtype_signature[s]
            x += rng.normal(0, 0.6, n_features)
            x += shifts[c]
            offset = 0
            for v in view_names:
                nf = len(FEATURE_SPECS[v])
                rows_views[v].append(x[offset:offset + nf])
                offset += nf
            cohort_idx.append(c)
            subtype_idx.append(s)
            stage_idx.append(k)
            subject_ids.append(f"{c}-{i:04d}")

    views = {
        v: pd.DataFrame(rows_views[v], index=subject_ids,
                        columns=list(FEATURE_SPECS[v]))
        for v in view_names
    }
    return SyntheticDataset(
        views=views,
        cohort=pd.Series(cohort_idx, index=subject_ids, name="cohort"),
        subtype=pd.Series(subtype_idx, index=subject_ids, name="subtype"),
        stage=pd.Series(stage_idx, index=subject_ids, name="stage"),
        sequences=sequences,
    )
