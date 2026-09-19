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

**Current status:** planning stage; AMP-PD DUA to be requested; no analysis has been run.

## What is included

| Path | Contents |
|---|---|
| `src/` | Multi-view clustering and SuStaIn-style utilities. |
| `tests/` | Synthetic tests. |
| `docs/` | Research status, methods scope, and contribution guidance. |

## Use and validation

```bash
python -m pytest -q
```

## Keywords

Parkinson's disease, AMP-PD, PPMI, subtyping, SuStaIn, multi-omics, reproducible research.

## Documentation

- [Introduction for new readers](docs/INTRODUCTION.md)
