# PD Multimodal Subtype Discovery (Paper 1)

This independent research repository plans and tracks multimodal Parkinson's disease subtype discovery (imaging + clinical + transcriptomics) with cross-cohort reproducibility in AMP-PD. It provides multi-view clustering utilities for transparent review and extension.

## Series position

This is **Paper 1** of the Parkinson's multimodal series (3 papers). It is the foundation of the series; Papers 2–3 build on its subtype definitions and harmonized dataset.

## Research plan

| Planned work | Expected outcome |
|---|---|
| AMP-PD access (free DUA via Terra) + harmonization of PPMI/PDBP/BioFIND | Versioned multimodal dataset (3,274 participants). |
| Multi-view subtype discovery (imaging + clinical events; SuStaIn-style) | Reproducible PD subtypes. |
| Cross-cohort reproducibility (PPMI vs. PDBP) | Replication report. |
| Release subtype assignments + harness | Reused by Papers 2–3. |

**Current status:** codebase scaffolded with synthetic-data validation; AMP-PD DUA to be requested; no real-data analysis has been run. See [docs/DATA_ACCESS.md](docs/DATA_ACCESS.md).

## What is included

| Path | Contents |
|---|---|
| `src/pd_subtypes/` | `harmonize` (cross-cohort z-scoring + ComBat-style batch correction), `sustain` (SuStaIn-style subtype-and-stage EM), `multiview` (per-view embeddings + consensus clustering), `reproducibility` (train-in-one-cohort/assign-in-another + agreement metrics), `simulate` (synthetic multimodal multi-cohort generator with planted subtypes). |
| `tests/` | Pytest suite validating the full pipeline on synthetic data (harmonization removes planted batch shifts; SuStaIn recovers planted subtypes; assignment transfers across cohorts). |
| `docs/` | Research status, AMP-PD data-access steps, methods scope, and contribution guidance. |
| `.github/` | CI workflow (pytest, Python 3.10–3.12), task issue template, and repo-card PR template. |

## Use and validation

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## Keywords

Parkinson's disease, AMP-PD, PPMI, subtyping, SuStaIn, multi-omics, reproducible research.

## Documentation

- [Introduction for new readers](docs/INTRODUCTION.md)
- [AMP-PD data access](docs/DATA_ACCESS.md)
- [Contributing](CONTRIBUTING.md)
