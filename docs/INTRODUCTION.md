# Introduction — PD Multimodal Subtype Discovery

**Series note:** This is **Paper 1 of 3** in the Parkinson's disease (PD) multimodal subtyping series. It is the **foundation paper**: it discovers and validates data-driven PD subtypes in AMP-PD that Paper 2 (`pd-progression-prediction-stratification`) and Paper 3 (`pd-blood-transcriptomic-proxy`) directly reuse.

## Background

Parkinson's disease is clinically and biologically heterogeneous; progression rates and treatment needs vary widely between patients. AMP-PD integrates clinical, imaging (MRI/DaTscan), CSF/blood biospecimen, and genomic data across PPMI, PDBP, BioFIND, and LCC, enabling multimodal data-driven subtyping at unprecedented scale.

## Research questions

1. How many reproducible multimodal PD subtypes exist across AMP-PD cohorts?
2. Do disease-course subtyping methods (SuStaIn) and multi-view clustering converge on similar structure?
3. Do subtypes replicate across independent cohorts (train in PPMI, test in PDBP/BioFIND)?

## Data

| Dataset | Size | Content | Access |
| --- | --- | --- | --- |
| AMP-PD Tier 2 (PPMI/PDBP/BioFIND/LCC) | ~4,000+ participants | Clinical (MDS-UPDRS, MoCA), MRI, DaTscan, CSF, genomics | DUA via Terra platform |

## Methods

- Harmonize clinical/imaging/CSF features across the four cohorts.
- SuStaIn (Subtype and Stage Inference) for disease-course subtypes; multi-view clustering as comparator.
- Cross-cohort reproducibility: discover in PPMI, assign and validate in PDBP/BioFIND.

## Expected contributions

- Validated multimodal PD subtypes with open assignment code — the shared foundation of Papers 2 and 3.
- A reproducibility audit of PD subtyping across cohorts.

## Scope and boundary

- Discovery/validation only; progression prediction is Paper 2, transcriptomic proxies are Paper 3.
- No wet-lab data generation; public/Tier 2 data only.
