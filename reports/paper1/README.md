# Paper 1 results package (semi-synthetic demo track)

One-command regeneration of Paper 1 Tables 1–3 and the demo cross-cohort
figure from the committed artifacts in `reports/`
(`qc_report_semisynthetic.csv`, `subtype_counts_by_cohort.csv`,
`subtyping_summary.json`):

```bash
python reports/paper1/make_tables.py && python reports/paper1/make_figures.py
```

Both scripts derive every number from the committed artifacts (nothing is
typed by hand), refuse to render if the artifacts disagree with each other,
and regenerate their outputs byte-identically (enforced by
`tests/test_paper1_package.py`).

| File | Contents |
|---|---|
| `make_tables.py` | Renders `tables_1_to_3_semisynthetic.md` (Tables 1–3 of `docs/RESULTS.md`). |
| `make_figures.py` | Renders `figure2_cross_cohort_demo.svg` (demo-track companion of the planned real-data Figure 2). |
| `tables_1_to_3_semisynthetic.md` | Rendered Tables 1–3 (semi-synthetic stand-in — **not real participant data**). |
| `figure2_cross_cohort_demo.svg` | Demo cross-cohort reproducibility figure (semi-synthetic stand-in). |

Scope note (issue #15): this is the semi-synthetic demo track of the Paper 1
figure/table scripts. The real-data main-result figures/tables remain gated
on #8 (subtype assignment release) ← #3 ← #5 (AMP-PD Tier 2 DUA); the
scripts' artifact-loading and rendering logic is designed to be pointed at
the real artifacts unchanged once they exist.
