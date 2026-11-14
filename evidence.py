"""Transparent, manually verified review evidence. No scraping or fabricated reviews."""
import json
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ALLOWED = {'reddit', 'youtube', 'retailer', 'independent_review', 'manufacturer'}
ISSUES = {'battery', 'heating', 'camera', 'display', 'software', 'network', 'build', 'performance', 'service', 'other'}


def load_evidence(path=None):
    path = Path(path or Path(__file__).with_name('reviews.json'))
    try:
        records = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return [], ['Review evidence file missing or invalid.']
    valid, warnings, seen = [], [], set()
    for i, r in enumerate(records):
        try:
            assert isinstance(r, dict)
            assert r['source_type'] in ALLOWED
            assert isinstance(r['model'], str) and r['model'].strip()
            assert isinstance(r['summary'], str) and len(r['summary'].strip()) >= 12
            assert r['sentiment'] in ('positive', 'mixed', 'negative')
            assert r['topic'] in ISSUES
            u = urlparse(r['url'])
            assert u.scheme == 'https' and u.netloc and '.' in u.netloc
            d = date.fromisoformat(r['date'])
            assert d <= date.today()
            key = (r['model'].casefold().strip(), r['url'].rstrip('/'))
            assert key not in seen
            seen.add(key)
            r = dict(r)
            r['date'] = d.isoformat()
            valid.append(r)
        except (AssertionError, KeyError, TypeError, ValueError):
            warnings.append(f'Ignored invalid or duplicate evidence entry #{i+1}.')
    return valid, warnings


def evidence_for(model, records):
    return [r for r in records if r['model'].casefold().strip() == model.casefold().strip()]


def summarize(records):
    """Describe evidence coverage, NOT failure rates or a statistically valid owner score."""
    sources = sorted(set(r['source_type'] for r in records))
    negatives = {}
    for r in records:
        if r['sentiment'] == 'negative':
            negatives[r['topic']] = negatives.get(r['topic'], 0) + 1
    # Explicitly do not equate post count with unique owners or failure incidence.
    if not records:
        confidence = 'No review evidence'
    elif len(records) >= 8 and len(sources) >= 3:
        confidence = 'Broader evidence coverage (not verified reliability)'
    elif len(records) >= 3 and len(sources) >= 2:
        confidence = 'Limited cross-source evidence'
    else:
        confidence = 'Very limited evidence'
    return {'confidence': confidence, 'sources': sources, 'issues': negatives, 'count': len(records)}
