# Evidence pipeline (curated measurements)

The engine now stores original external test measurements, **not automatically generated /10 scores**. This protects against comparing unlike testing protocols and prevents model-level confidence inflation.

## Import

1. Research a source and verify the *exact phone*, variant, test conditions and measurement.
2. Enter a row into `observations_template.csv` (or another CSV with the same headers). Use the **original numeric value and unit** (e.g. `20.82`, `hours`; `151`, `DXOMARK points`).
3. Run `python evidence_pipeline.py import your_observations.csv`.
4. Run `python evidence_pipeline.py validate` and `python -m unittest discover -v`.
5. Inspect the source link and result in the app's Evidence & Audit Trail.

Required fields: `brand,model,pillar,source,metric,value,unit,url,tested_on`.
Optional fields: `variant,test_conditions,notes`.

Supported sources: dxomark, phonearena, nanoreview, geekbench, 3dmark, notebookcheck, gsmarena, official, other. Only HTTPS URLs accepted. A source label alone does not verify the measurement; a reviewer must check the linked page.

## Scoring and verification rules

- **No cross-site average** until test protocols and units are normalized and calibration anchors are documented.
- Raw observations are **visible in the app**, but do not overwrite verified model scores or inferred specification scores.
- Model-level /10 scores still require independent source-linked assessment and calibration; component-level estimates remain provisional.
- A source may publish different scores under updated protocols. Record `tested_on` and test conditions; do not assume cross-protocol equivalence.
- Current India prices must be recorded separately with variant, seller, checked date and URL before claiming market-relative value.
- Do not automatically scrape copyrighted benchmark tables or republish complete reviews without permission.

## Coverage and readiness

A model is **evidence-researched** when it has real measurements for the relevant pillars, not simply an inferred `estimated_score`. A phone is **rating-verified** only after all four pillar ratings are independently calibrated and reviewed. The release remains provisional until that threshold is met.
