# Reddit + approved YouTube reviewer feedback

## Approved channels only

Gyan Therapy and GeekyRanjit are the **only** approved YouTube reviewers. The app searches via YouTube Data API v3 `search.list` with `channelId` and checks the `snippet.channelId` returned for every video. It does not accept title/name matches alone. Search uses API quota, and results may be incomplete.

In Streamlit Secrets, preserve the existing `YOUTUBE_API_KEY`, and add these after independently verifying each channel's ID on its official YouTube channel:

```toml
GYAN_THERAPY_CHANNEL_ID = "<verified channel ID>"
GEEKYRANJIT_CHANNEL_ID = "<verified channel ID>"
```

Do not use guessed channel IDs. The application intentionally disables discovery until both are configured. The YouTube Data API does **not** automatically provide transcripts for other creators' videos. The discovery UI therefore displays links and titles only; it does not invent reviewer opinions.

## Evidence data

`owner_feedback.json` contains `youtube` and `reddit` arrays. An entry must include:

- `model_slug`: canonical phone ID from `catalog.slugify_model`.
- `url`: direct HTTPS YouTube video or Reddit post link.
- `pillar`: performance, camera, battery, display, reliability, or software.
- `finding`: concise, checked observation; never infer from a title or a lone comment.
- `verified_from_content`: `true` only after someone actually checks the source.
- For YouTube: `reviewer` exactly `Gyan Therapy` or `GeekyRanjit` and the matching verified `channel_id`.

Recommended optional fields: `published`, `observed_at`, `timestamp`, `context`, `evidence_type`, `sample_size`, `limitations`.

Example **SCHEMA ONLY, NOT A REAL REVIEW**:

```json
{
  "model_slug": "example_phone",
  "url": "https://www.reddit.com/r/example/comments/example/example/",
  "pillar": "battery",
  "finding": "Example only: report of standby drain after a software update",
  "verified_from_content": false
}
```

## Reddit access and reliability

For the initial release, add manually reviewed, publicly accessible Reddit links; do not run an unapproved bulk scraper. If an approved Reddit API integration is available later, obey its terms and rate limits. One post is an anecdote, not proof of a systemic issue. Record dates, firmware versions and independent corroboration. Keep personally identifying details out of the evidence database.

## Scoring boundary

Owner and reviewer findings appear **separately** from the numerical four-pillar scores. They do not change ratings automatically. A future reliability model requires a published rubric, independent corroboration, and a representative sample.
