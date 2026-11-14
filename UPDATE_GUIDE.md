# Phone Rating Engine v4 — source-assisted discovery

**What changed:** Unknown phones now get official-source search links, an optional manufacturer URL reader, partial evidence-based spec display, and live YouTube review discovery. No API key is needed for source links. Your existing `YOUTUBE_API_KEY` secret is reused.

**What is NOT provided:** There is no universal free manufacturer specs API, automatic full ratings for every model, or validated automatic Reddit/YouTube sentiment. Some official sites block automated requests; use links in that case. Exact variant confirmation remains essential.

## Android / GitHub update

1. Extract ZIP. Open repository `vhora34/phone-rating-engineo` on GitHub in Chrome Desktop site.
2. Upload `source_lookup.py` as a new file.
3. Replace existing `app.py` with the included version (edit file or GitHub upload).
4. Ensure `requirements.txt` contains `streamlit`, `requests`, `beautifulsoup4`. Existing version is already sufficient.
5. Keep `engine.py`, `lookup.py`, `ownership.py`, `evidence.py`, `youtube_reviews.py` unchanged.
6. Commit and wait for Streamlit to redeploy.
7. Try `iQOO 15R`, price `49000` if that's what you meant. Use official-source search, paste the exact manufacturer's specs page if found, and click `Read specification page`. Click `Find YouTube reviews` separately.

**Safety:** Do not publish API keys in GitHub. The page reader restricts input to public HTTPS and blocks private/local IPs, redirects, and oversized content. For production-grade deployment, stronger DNS rebinding protection or a fixed allowlist of manufacturer domains is recommended.
