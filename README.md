# Phone Rating Engine — evidence-tier prototype

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
python -m unittest -v test_scoring
```

## Inspected source schemas

- `smartphones_2025_specs.csv`, `smartphones_2026_specs.csv`: `id,brand,model,release_month,os,processor,ram_gb,storage_gb,display_size_in,display_type,rear_camera,front_camera,battery_mah,charging_w,launch_price_inr,launch_price_usd`.
- `historical_models_catalog.csv`: `brand,model,full_name,data_status,specifications_source,notes`.
- Original `evidence.json` was `[]`, with **no measurements**. The new schema is `{"models":{},"components":{"chipsets":{},"camera_sensors":{}}}`.

## Source-linked evidence schema

```json
{
  "models": {
    "samsung_galaxy_s25_ultra": {
      "performance": {
        "score": 8.5,
        "note": "Explain measurement and scoring conversion here",
        "sources": [{"title": "Actual independent test title", "url": "https://actual-source.example/test"}]
      }
    }
  },
  "components": {
    "chipsets": {
      "Qualcomm Snapdragon 8 Elite": {
        "performance": {
          "score": 8.3,
          "note": "SoC benchmark baseline; not phone-specific thermal test",
          "sources": [{"title": "Actual benchmark source", "url": "https://actual-source.example/benchmark"}]
        }
      }
    },
    "camera_sensors": {}
  }
}
```

The JSON example above is **illustrative only**; it is not included as actual evidence. Do not add placeholder URLs or arbitrary ratings to production data. Source URLs are checked for HTTPS format, but authenticity and scoring validity require human review.

## Scoring policy

- Four equally weighted pillars: performance, camera, battery, display.
- Tier 1: model-specific numeric scores **with source links**.
- Tier 2: chipset performance or explicitly identified primary camera sensor with source links. Generic `50MP` camera strings **are not sensor identifiers**.
- Tier 3: conservative, unvalidated specification proxies. RAM is not a processor benchmark; megapixels are not image-quality scores; battery mAh is not tested endurance.
- Missing pillar: `None`, not zero. Full rating absent unless all four pillars have at least a proxy.
- Confidence is the weakest pillar tier. Labels describe *evidence type*, not proof that a cited study is accurate.
- RAM/storage changes apply only a small performance/multitasking proxy, not a CPU benchmark increase. Storage speed/type is not present in the provided CSVs.
- Price brackets: Budget below ₹15k, Mid-Range ₹15k–₹30k, Upper Mid-Range ₹30k–₹50k, Flagship ₹50k+.
- Market average is based only on **three or more other fully model-evidenced phones** in the same CSV launch-price bracket. It is not estimated from raw-spec proxy scores. The user-selected variant price determines its bracket. Price comparisons remain indicative until verified current prices and exact variant prices are added.
- `base_model_price` uses CSV launch price as a provisional reference, **not an independently confirmed base-variant market price**. Therefore storage markup is an indicative proxy until actual variant prices are supplied.
- Categorization uses within-phone pillar spread and distance from its own mean; this is descriptive and should not be interpreted as a certified gaming or camera ranking.

## Important deployment warning

This is a **functional prototype**, not a calibrated purchasing-grade rating model. The CSVs have not been independently verified, and `evidence.json` intentionally contains no invented observations. Consequently, current numeric scores may be spec-only proxies, and market value verdicts will be unavailable until verified peers are added. Verify source authenticity, regional variants, camera image-quality methodology, real endurance, current prices, and score normalization before production use.


## DXOMARK camera evidence (manual, cited)
Four exact model matches now contain `external_tests.dxomark_camera` with original raw score, test protocol, date, source URL, and concise findings. The app shows these independently of the provisional /10 pillar score. **No automatic raw-score conversion or scraping is performed.** DXOMARK Camera v5 and v6 protocols must not be pooled without a validated crosswalk. Source entries in `camera.sources` alone do not qualify an inferred `estimated_score` as a verified model-level `score`. Other models remain without DXOMARK coverage until individually checked.
