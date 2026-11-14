# Phone Rating Engine v3

A free Streamlit demo combining a curated editorial smartphone database, buyer suitability profiles, five-year battery ageing *scenarios*, and **source-linked, manually reviewed** Reddit/YouTube/retailer evidence.

## Deploy / update

Upload these files at the **root** of your existing GitHub repository, replacing previous versions: `app.py`, `engine.py`, `lookup.py`, `ownership.py`, `evidence.py`, `reviews.json`, `requirements.txt`. Streamlit Community Cloud should redeploy from `main` automatically.

## Add reviews

`reviews.json` starts as `[]`: no real review claims are fabricated. Add entries with these fields:

```json
[
  {
    "model": "Samsung Galaxy S25",
    "source_type": "youtube",
    "url": "https://www.youtube.com/watch?v=REPLACE_WITH_REAL_VIDEO",
    "date": "2026-11-01",
    "topic": "battery",
    "sentiment": "mixed",
    "summary": "Replace this with your own accurate, checked summary of the actual video."
  }
]
```

The above is a **template**, not evidence. Use real URLs, dates and your own independently verified summaries. Accepted source types: reddit, youtube, retailer, independent_review, manufacturer. Topics: battery, heating, camera, display, software, network, build, performance, service, other. Sentiments: positive, mixed, negative.

The Reviews tab also provides links to search Reddit, YouTube and Google for that model. **Those links are not automatic review analysis**. Automated ingestion would require compliant APIs/data licenses and quality controls.

## Scoring caveats

- Existing hardware ratings remain subjective editorial scores from v2. They have not been independently calibrated.
- Gaming suitability uses everyday-performance proxies, **not GPU benchmarks, sustained FPS or throttling measurements**.
- Battery ageing chart shows hypothetical 3%, 6%, 10% yearly loss, not a phone-specific prediction.
- Online negative mentions are not verified failure rates.
- Unknown phones receive a cautious Wikipedia lookup and partial heuristic estimates, **not** a full score.
- Review evidence is displayed separately; it does not secretly change hardware ratings.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Live YouTube discovery

In Streamlit Community Cloud → App settings → Secrets, set `YOUTUBE_API_KEY = "your_key"` (never commit this secret to GitHub). In the Reviews & sources tab, tap **Find YouTube reviews**. Search metadata and optional public comments are shown with source links. Search costs approximately 100 YouTube API quota units; the app caches searches for 7 days per model. Comments may be disabled and are not representative. No transcript extraction or sentiment scoring is performed. `youtube_reviews.py` must be uploaded alongside `app.py`.
