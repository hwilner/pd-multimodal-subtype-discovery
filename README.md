# PD Multimodal Subtype Discovery 

This independent research repository plans and tracks multimodal Parkinson's disease subtype discovery (imaging + clinical + transcriptomics) with cross-cohort reproducibility in AMP-PD. It provides multi-view clustering utilities for transparent review and extension.

## Introduction

Parkinson's disease is clinically and biologically heterogeneous, and that heterogeneity is one reason trials and prognostic models struggle: cohort averages hide subgroups with different progression courses. This repository (Paper 1 of the PD series) discovers multimodal PD subtypes from imaging, clinical, and CSF features and tests whether they **replicate across independent cohorts** (discover in PPMI, test in PDBP/BioFIND/LCC) inside AMP-PD. See [docs/INTRODUCTION.md](docs/INTRODUCTION.md) for the full introduction, research questions, and scope.

## Extended introduction

For readers with no background in the area — what PD subtyping is, why SuStaIn-style disease-course modelling and multi-view clustering are used, why cross-cohort replication is the bar, and how AMP-PD/Terra data access works — see [docs/EXTENDED_INTRODUCTION.md](docs/EXTENDED_INTRODUCTION.md) (with a concept figure in `docs/figures/`). Data-use terms and the access path are documented in [docs/DATA_ACCESS.md](docs/DATA_ACCESS.md).

## Materials and methods

Design decisions, rationale, and scope are pre-registered in [docs/METHODS.md](docs/METHODS.md): harmonize *within cohort* before pooling (z-scoring + ComBat-style location/scale correction); SuStaIn subtype-and-stage EM **triangulated** against a multi-view consensus-clustering comparator; nearest-centroid assignment for cross-cohort transfer; ARI + subtype-signature correlation as the reproducibility metrics; k chosen by cross-validated likelihood; a parametric-vs-non-parametric decision guide; and the discover-in-one-cohort/test-in-another anti-leakage rule.

**Research plan (issue-mapped, with dependencies).** All work is tracked as atomic GitHub issues with `Depends on`/`Blocked by` notes in each body.

| Issue | Task | Size | Depends on |
|---|---|---|---|
| #5 | Obtain AMP-PD Tier 2 DUA via Terra | S | — (ready) |
| #9 | Common cross-cohort feature table and mappings | S | #5 |
| #14 | Cross-cohort batch-effect correction pipeline | S | #9 |
| #17 | Harmonization QC report | XS | #14 |
| #2 | Harmonize clinical/imaging/CSF across cohorts (umbrella) | L | #5 |
| #6 | Subtyping feature-set freeze | XS | #2 |
| #12 | SuStaIn subtype/stage solutions with CV likelihood | S | #6 |
| #10 | Multi-view clustering comparator run | S | #6 |
| #16 | SuStaIn vs multi-view agreement quantification | XS | #12, #10 |
| #4 | SuStaIn multi-view subtyping (umbrella) | L | #2 |
| #7 | PPMI subtype assignment model | S | #4 |
| #11 | Apply assignment model to held-out cohorts | S | #7 |
| #18 | Cross-cohort reproducibility metrics and validation report | XS | #11 |
| #3 | Cross-cohort reproducibility validation (umbrella) | M | #4 |
| #8 | Subtype assignment release (CSV + assignment code) | S | #3 |
| #15 | Paper 1 figure scripts | S | #8 |
| #13 | Paper 1 manuscript draft | S | #8 |
| #20 | Handoff README for Papers 2 and 3 | S | #8 |
| #1 | Release subtype assignments + writeup (umbrella) | M | #3 |
| #19 | Paper 1 reproducibility re-run | S | #15 |

## Results

Results live in [docs/RESULTS.md](docs/RESULTS.md) as captioned, paper-style tables and figures: Tables 1–3 are completed from the committed semi-synthetic validation run (`reports/`); Tables 4–8 and Figures 1–2 are pre-registered placeholders, each linked to the issue that authorizes filling it in. A code-level verification record (test-suite verdicts) is kept in the root [results.md](results.md) and extended as Table 9 of `docs/RESULTS.md`.

**Table 1 (headline). Cross-cohort subtype transfer on the semi-synthetic stand-in** — a documented generator built from published summary statistics, **not real participant data** (see `docs/DATA_ACCESS.md`). SuStaIn trained on PPMI (240 subjects, 12 features, k = 2 recovered); held-out cohorts assigned by nearest-centroid. Full detail: [docs/RESULTS.md](docs/RESULTS.md), Table 3.

| Metric | PDBP | BioFIND |
|---|---|---|
| Assignment ARI vs. planted labels | 0.950 | 1.000 |
| Subtype-signature correlation | 0.997 | 0.990 |

No real-data analysis has been run yet: it is gated on the AMP-PD Tier 2 DUA (issue #5). The modest SuStaIn-vs-consensus agreement on the stand-in (ARI 0.41) is recorded honestly in `docs/RESULTS.md` Table 3.

**Current status:** codebase scaffolded with synthetic-data validation; the AMP-PD Terra staging pipeline (`pd_subtypes.amppd` + `scripts/`) is implemented and the full harmonize → SuStaIn → cross-cohort pipeline has been validated end-to-end on a documented semi-synthetic stand-in built from published summary statistics (see `reports/`); AMP-PD Tier 2 DUA to be requested; no real-data analysis has been run. See [docs/DATA_ACCESS.md](docs/DATA_ACCESS.md).

## What is included

| Path | Contents |
|---|---|
| `src/pd_subtypes/` | `harmonize` (cross-cohort z-scoring + ComBat-style batch correction), `sustain` (SuStaIn-style subtype-and-stage EM), `multiview` (per-view embeddings + consensus clustering), `reproducibility` (train-in-one-cohort/assign-in-another + agreement metrics), `simulate` (synthetic multimodal multi-cohort generator with planted subtypes), `amppd` (Terra export staging: expected `<COHORT>_<view>.tsv` layout, alignment/integrity QC, feature-matrix construction; raises a clear access error when no export is present; includes a documented semi-synthetic generator from published summary statistics). |
| `scripts/prepare_amppd.py` | One-command staging of a Terra export (`--terra-export`) or the semi-synthetic stand-in (`--semi-synthetic`) into per-view feature matrices + `qc_report.csv`. |
| `scripts/run_subtyping.py` | One-command pipeline: harmonize → SuStaIn subtypes/stages → multi-view consensus comparator → cross-cohort reproducibility; writes `reports/subtype_assignments.csv` + `reports/subtyping_summary.json`. |
| `tests/` | Pytest suite validating the full pipeline on synthetic data (harmonization removes planted batch shifts; SuStaIn recovers planted subtypes; assignment transfers across cohorts) plus Terra-export staging tests on semi-synthetic fixtures. |
| `reports/` | Small derived results from the semi-synthetic validation run (QC report, per-cohort subtype counts, summary metrics). Not real participant data. |
| `reports/paper1/` | Paper 1 results package (demo track): one-command regeneration of Tables 1–3 and the demo cross-cohort figure from the committed artifacts (`make_tables.py` / `make_figures.py`), byte-parity tested. |
| `docs/` | Research status, AMP-PD data-access steps, methods scope, and contribution guidance. |
| `.github/` | CI workflow (pytest, Python 3.10–3.12), task issue template, and repo-card PR template. |

## Use and validation

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Latest verification: **23 passed / 0 failed** on `main` (2026-11-18, Python 3.12; see `docs/RESULTS.md` Table 9). CI runs the same suite on Python 3.10–3.12 (`.github/workflows/ci.yml`).

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
- [Results (captioned tables and figures)](docs/RESULTS.md)
- [AMP-PD data access](docs/DATA_ACCESS.md)
- [Contributing](CONTRIBUTING.md)
