# Results — PD Multimodal Subtype Discovery (Paper 1)

Results are reported as captioned, paper-style tables and figures. Tables 1–3
are **completed from the committed semi-synthetic validation run** in
`reports/` (a documented stand-in built from published summary statistics —
**not real participant data**; see `docs/DATA_ACCESS.md`). Tables 4–8 and
Figures 1–2 are **pre-registered placeholders**: their structure and the
metrics they will report are fixed here in advance, each linked to the issue
that authorizes filling it in. Table 9 records code-level validation.

## Completed results (semi-synthetic validation run)

**Table 1. Semi-synthetic cohort × view inventory and QC.** Per-view feature
matrices staged by `scripts/prepare_amppd.py --semi-synthetic` and validated
by the test suite (issue #2 acceptance-criteria rehearsal on the stand-in).
Source: `reports/qc_report_semisynthetic.csv`. No missing values and no
constant features in any cohort × view block.

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

**Table 2. Recovered subtype counts by cohort (semi-synthetic).** SuStaIn
recovered k = 2 subtypes on the harmonized stand-in; per-cohort counts are
balanced and median assigned stage is identical across cohorts, as expected
for a stand-in with no cohort-specific prevalence. Source:
`reports/subtype_counts_by_cohort.csv`.

| Cohort | Subtype 0 | Subtype 1 | Median stage |
|---|---|---|---|
| PPMI | 36 | 44 | 5.0 |
| PDBP | 46 | 34 | 5.0 |
| BioFIND | 44 | 36 | 5.0 |

**Table 3. Subtyping run summary and cross-cohort transfer (semi-synthetic).**
Pipeline: harmonize → SuStaIn (train cohort PPMI) → multi-view consensus
comparator → nearest-centroid assignment to held-out cohorts. Source:
`reports/subtyping_summary.json`. Assignment ARI is against planted subtype
labels (available because the stand-in is synthetic). The modest
SuStaIn-vs-consensus ARI (0.41) is recorded honestly: the two methods recover
related but non-identical partitions on the stand-in — agreement
quantification on real data is pre-registered in Table 6 (issue #16), and the
divergence is itself a triangulation finding to revisit once #12/#10 land.

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

## Pre-registered results (real-data, issue-gated)

**Table 4. Harmonization QC report (real AMP-PD data).** _Placeholder._ Rows:
cohort × view blocks (PPMI, PDBP, BioFIND, LCC); columns: n subjects,
n features, fraction missing, constant features, pre-/post-correction batch
diagnostics. Authorized by issues #9 → #14 → #17 (feature table → batch-effect
correction → QC report), gated on #5 (Tier 2 DUA) → #2.

**Table 5. SuStaIn subtype/stage solutions with cross-validated likelihood.**
_Placeholder._ Rows: candidate k; columns: CV log-likelihood, held-out
log-likelihood, selected k per the decision rule in `docs/METHODS.md`.
Authorized by issue #12 (under umbrella #4), after feature freeze #6.

**Table 6. SuStaIn vs. multi-view clustering agreement.** _Placeholder._
Columns: ARI, per-subtype confusion summary, interpretation per the
triangulation rule in `docs/METHODS.md`. Authorized by issue #16, after
#12 (SuStaIn) and #10 (multi-view comparator).

**Table 7. Cross-cohort reproducibility metrics.** _Placeholder._ Columns per
held-out cohort (PDBP, BioFIND, LCC): assignment ARI, subtype-signature
correlation, pass/fail against the pre-registered reproducibility thresholds.
Authorized by issue #18, via #7 → #11 (assignment model → held-out
application), feeding umbrella #3.

**Table 8. Paper 1 results package.** _Placeholder._ Released subtype
assignments CSV + assignment code (#8), figure panels (#15), manuscript
tables (#13), handoff summary for Papers 2–3 (#20), umbrella release and
writeup (#1).

**Figure 1 (planned).** Subtype progression patterns: per-subtype biomarker
event orderings with positional-variance diagrams from the selected SuStaIn
solution. Authorized by issues #12 → #15.

**Figure 2 (planned).** Cross-cohort reproducibility: assignment agreement and
signature correlations across held-out cohorts, with pre-registered
thresholds marked. Authorized by issues #18 → #15.

## Validation record

**Table 9. Test-suite validation record.** Cheap suite run per branch on every
programme visit. The 2026-11-02 row reproduces the record in the root
`results.md` (committed by a CI-hardening pass outside this programme).

| Date | Branch @ commit | Result | Wall clock | Environment |
|---|---|---|---|---|
| 2026-11-02 | main (CI-hardening pass) | 13 passed / 0 failed / 0 skipped | 6.6 s | Python 3.11, CPU |
| 2026-11-03 | main @ 1f92412 | **13 passed / 0 failed / 0 skipped** | 2.6 s | Python 3.12.12, CPU, numpy 2.2.5, pandas 2.3.2, scipy 1.16.2, scikit-learn 1.7.2, pytest 9.2.0 |

Heavy compute (real AMP-PD harmonization #2/#14, SuStaIn grid #12, cross-cohort
validation #3/#18, reproducibility re-run #19): **deferred (needs
environment/data — AMP-PD Tier 2 DUA, issue #5)**.

## What this does NOT establish

- The semi-synthetic run validates the **pipeline**, not any scientific claim
  about Parkinson's disease subtypes; it is a stand-in from published summary
  statistics, not participant data.
- A passing unit suite is evidence of internal code consistency only (see
  root `results.md` for the full caveat list this table extends).
