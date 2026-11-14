# CSV catalog integration (v4.1)

Upload these **four** files to the root of your existing GitHub repository:
- `app.py` (replace existing file)
- `specs_catalog.py` (new)
- `smartphones_2025_specs.csv` (new)
- `smartphones_2026_specs.csv` (new)

Keep the other Python files and `requirements.txt` already deployed from v4.

The catalog uses exact normalized model-name matching; it deliberately does not merge close model names or generate unsupported overall ratings. Some rows are future-dated and may be speculative. OnePlus 15 appears in both CSVs and is displayed as two entries for comparison, rather than silently choosing one. These CSVs are user-supplied and unverified; cross-check the precise regional variant with manufacturer pages before purchasing.

For a completely fresh deployment, upload all source files in this ZIP to your repository root. Keep your YouTube key in Streamlit Secrets, never in GitHub.
