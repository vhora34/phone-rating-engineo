# Phone Rating Engine v5 — expanded model recognition

Added 337 historical model-name entries across 18 brands. The two original user-supplied 2025/2026 specification CSVs are retained unchanged. The historical catalog has NO specifications or ratings; its names are discovery candidates only, and are not independently verified.

## Android / GitHub update

Upload or replace `app.py`, and add `historical_catalog.py` and `historical_models_catalog.csv` to the repository root. If you have not deployed v4.1, upload the entire ZIP's app files and both supplied specification CSVs instead. Keep `YOUTUBE_API_KEY` in Streamlit Secrets.

## Scope

This is not a live manufacturer-specification API or a database of verified phone benchmarks. Names and regional variants can be incomplete or ambiguous. The app deliberately does not fabricate a score for these entries.
