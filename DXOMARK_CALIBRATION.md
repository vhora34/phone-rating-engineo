# DXOMARK relative-reference policy

- DXOMARK publishes original raw camera, photo and video scores. Preserve these in their original units and protocol.
- The screenshot of Motorola Signature shows camera 164 vs a displayed best 175, photo 170 vs 180, video 154 vs 176. These are **screenshot observations**, not a verified, versioned global calibration table.
- Relative indicator = `100 * device_raw_score / fixed_reference_raw_score`, but only when metric and testing protocol match, and reference source URL and date are recorded.
- A fixed reference is **not** the theoretical maximum; percentages may exceed 100. Never label this as a /10 quality rating, and never mix it into the four-pillar composite automatically.
- No calibrated reference has been enabled in `evidence.json`. To enable one, first verify an authoritative page, record the date and protocol, then insert e.g. `"dxomark_references": {"camera_v6": {"camera": {"score": 175, "metric": "camera", "protocol": "camera_v6", "source_url": "https://www.dxomark.com/...", "as_of": "YYYY-MM-DD"}}}`.
- Different protocols, missing dates or references must yield “unavailable” rather than an invented score.
- To produce a defensible 0–10 quality score later, fit and validate a transparent mapping against a sufficiently large, protocol-consistent device cohort and independent test outcomes; do not use ratio-to-best as the sole quality model.
