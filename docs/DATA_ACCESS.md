# AMP-PD Data Access (Tier 2)

This project analyzes the Accelerating Medicines Partnership Parkinson's
Disease (AMP-PD) Tier 2 dataset, which harmonizes PPMI, PDBP, BioFIND,
and the LCC (LRRK2 Cohort Consortium). All real-data tasks in this
repository are **blocked until Tier 2 access is granted**.

## Access steps

1. **Register** on the AMP-PD Knowledge Platform
   (https://www.amp-pd.org) and review the Data Use Agreement (DUA).
2. **Apply for Tier 2 access**: submit the Tier 2 application,
   including institutional affiliation, a brief research description
   (multimodal PD subtype discovery), and agreement to the AMP-PD
   Data Use Terms and publication policy.
3. **Wait for approval** by the AMP-PD Data Access Committee (typically
   a few weeks; may require institutional sign-off).
4. **Set up a Terra workspace**: once approved, log in to Terra
   (https://app.terra.bio) with the approved identity, clone or create
   an AMP-PD Tier 2 workspace, and confirm access to the PPMI, PDBP,
   BioFIND, and LCC tables (clinical, imaging, DaTscan, CSF).
5. **Configure a cloud environment** in Terra (notebook runtime or
   workflow) with Python >= 3.10 and this package installed.

## Data-use terms (summary)

- Tier 2 data are controlled-access; do not redistribute or commit
  participant-level data or derived subject-level identifiers anywhere,
  including this repository.
- All analyses run inside the Terra workspace; only aggregate,
  non-identifying results (e.g., subtype statistics, QC metrics) may be
  exported, subject to AMP-PD export review.
- Publications must acknowledge AMP-PD and the contributing cohorts and
  follow the AMP-PD publication policy.

## Current status

- [ ] Tier 2 application approved (owner action required — see issue
      "Obtain AMP-PD Tier 2 DUA via Terra")
- [ ] Terra workspace configured for PPMI/PDBP/BioFIND/LCC
- [ ] Data-use terms summarized here (initial summary above; to be
      finalized against the executed DUA)

**Until access is granted, all pipeline code is developed and tested on
synthetic data (`pd_subtypes.simulate`); real-data tasks are blocked.**
