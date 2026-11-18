# Paper 1 Tables 1-3 (semi-synthetic validation run)

Rendered by `reports/paper1/make_tables.py` from committed artifacts
(`reports/qc_report_semisynthetic.csv`,
`reports/subtype_counts_by_cohort.csv`,
`reports/subtyping_summary.json`). Semi-synthetic stand-in from
published summary statistics - **not real participant data** (see
`docs/DATA_ACCESS.md`). Do not edit by hand; regenerate.

**Table 1. Semi-synthetic cohort × view inventory and QC.**

| Cohort | View | Subjects | Features | Frac. missing | Constant features |
|---|---|---|---|---|---|
| PPMI | clinical | 80 | 4 | 0.0 | 0 |
| PPMI | imaging | 80 | 3 | 0.0 | 0 |
| PPMI | datscan | 80 | 2 | 0.0 | 0 |
| PPMI | csf | 80 | 3 | 0.0 | 0 |
| PDBP | clinical | 80 | 4 | 0.0 | 0 |
| PDBP | imaging | 80 | 3 | 0.0 | 0 |
| PDBP | datscan | 80 | 2 | 0.0 | 0 |
| PDBP | csf | 80 | 3 | 0.0 | 0 |
| BioFIND | clinical | 80 | 4 | 0.0 | 0 |
| BioFIND | imaging | 80 | 3 | 0.0 | 0 |
| BioFIND | datscan | 80 | 2 | 0.0 | 0 |
| BioFIND | csf | 80 | 3 | 0.0 | 0 |
| **Total** | **4 views** | **240** | **12** | **0.0** | **0** |

**Table 2. Recovered subtype counts by cohort (semi-synthetic).**

| Cohort | Subtype 0 | Subtype 1 | Median stage |
|---|---|---|---|
| PPMI | 36 | 44 | 5.0 |
| PDBP | 46 | 34 | 5.0 |
| BioFIND | 44 | 36 | 5.0 |

**Table 3. Subtyping run summary and cross-cohort transfer (semi-synthetic).**

| Metric | Value |
|---|---|
| Subjects / features | 240 / 12 |
| Subtypes recovered (k) | 2 |
| SuStaIn log-likelihood | −4097.82 |
| SuStaIn vs. multi-view consensus ARI | 0.409 |
| PPMI → PDBP assignment ARI | 0.950 |
| PPMI → PDBP subtype-signature correlation | 0.997 |
| PPMI → BioFIND assignment ARI | 1.000 |
| PPMI → BioFIND subtype-signature correlation | 0.990 |
