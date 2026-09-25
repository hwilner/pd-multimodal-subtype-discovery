# PD Multimodal Subtype Discovery 

This independent research repository plans and tracks multimodal Parkinson's disease subtype discovery (imaging + clinical + transcriptomics) with cross-cohort reproducibility in AMP-PD. It provides multi-view clustering utilities for transparent review and extension.

## Research plan

| Planned work | Expected outcome |
|---|---|
| AMP-PD access (free DUA via Terra) + harmonization of PPMI/PDBP/BioFIND | Versioned multimodal dataset (3,274 participants). |
| Multi-view subtype discovery (imaging + clinical events; SuStaIn-style) | Reproducible PD subtypes. |
| Cross-cohort reproducibility (PPMI vs. PDBP) | Replication report. |
| Release subtype assignments + harness | Reusable by later work. |

**Current status:** codebase scaffolded with synthetic-data validation; the AMP-PD Terra staging pipeline (`pd_subtypes.amppd` + `scripts/`) is implemented and the full harmonize → SuStaIn → cross-cohort pipeline has been validated end-to-end on a documented semi-synthetic stand-in built from published summary statistics (see `reports/`); AMP-PD Tier 2 DUA to be requested; no real-data analysis has been run. See [docs/DATA_ACCESS.md](docs/DATA_ACCESS.md).

## What is included

| Path | Contents |
|---|---|
| `src/pd_subtypes/` | `harmonize` (cross-cohort z-scoring + ComBat-style batch correction), `sustain` (SuStaIn-style subtype-and-stage EM), `multiview` (per-view embeddings + consensus clustering), `reproducibility` (train-in-one-cohort/assign-in-another + agreement metrics), `simulate` (synthetic multimodal multi-cohort generator with planted subtypes), `amppd` (Terra export staging: expected `<COHORT>_<view>.tsv` layout, alignment/integrity QC, feature-matrix construction; raises a clear access error when no export is present; includes a documented semi-synthetic generator from published summary statistics). |
| `scripts/prepare_amppd.py` | One-command staging of a Terra export (`--terra-export`) or the semi-synthetic stand-in (`--semi-synthetic`) into per-view feature matrices + `qc_report.csv`. |
| `scripts/run_subtyping.py` | One-command pipeline: harmonize → SuStaIn subtypes/stages → multi-view consensus comparator → cross-cohort reproducibility; writes `reports/subtype_assignments.csv` + `reports/subtyping_summary.json`. |
| `tests/` | Pytest suite validating the full pipeline on synthetic data (harmonization removes planted batch shifts; SuStaIn recovers planted subtypes; assignment transfers across cohorts) plus Terra-export staging tests on semi-synthetic fixtures. |
| `reports/` | Small derived results from the semi-synthetic validation run (QC report, per-cohort subtype counts, summary metrics). Not real participant data. |
| `docs/` | Research status, AMP-PD data-access steps, methods scope, and contribution guidance. |
| `.github/` | CI workflow (pytest, Python 3.10–3.12), task issue template, and repo-card PR template. |

## Use and validation

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## One-command pipeline

With AMP-PD Tier 2 access (after DUA approval), export one TSV per cohort/view (e.g. `PPMI_clinical.tsv`, with a `subject_id` column) from your Terra workspace, then:

```bash
python scripts/prepare_amppd.py --terra-export /path/to/export --out data/prepared
python scripts/run_subtyping.py --prepared data/prepared
```

Without access (documented semi-synthetic stand-in from published summary statistics — not real data):

```bash
python scripts/prepare_amppd.py --semi-synthetic --out data/prepared
python scripts/run_subtyping.py --prepared data/prepared
```

The latest semi-synthetic run (240 subjects, 3 cohorts, 12 features; 2 subtypes recovered with cross-cohort assignment ARI ≈ 0.95–1.0) is in `reports/`.

## Keywords

Parkinson's disease, AMP-PD, PPMI, subtyping, SuStaIn, multi-omics, reproducible research.

## Documentation

- [Introduction for new readers](docs/INTRODUCTION.md)
- [Extended introduction (no background required)](docs/EXTENDED_INTRODUCTION.md)
- [Methods: decisions and rationale](docs/METHODS.md)
- [AMP-PD data access](docs/DATA_ACCESS.md)
- [Contributing](CONTRIBUTING.md)
