"""Source-linked reviewer and owner observations; no fabricated sentiment or scraping."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

REVIEWERS = ('Gyan Therapy', 'GeekyRanjit')
PILLARS = ('performance', 'camera', 'battery', 'display', 'reliability', 'software')
ROOT = Path(__file__).resolve().parent


def load_feedback(path=None):
    path = Path(path) if path else ROOT / 'owner_feedback.json'
    if not path.exists():
        return {'youtube': [], 'reddit': []}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Feedback database must be a JSON object')
    return {'youtube': data.get('youtube', []), 'reddit': data.get('reddit', [])}


def validate_feedback(entry, platform, approved_channels=None):
    """Validate manual, attributable findings; never derive opinions from titles."""
    if platform not in ('youtube', 'reddit') or not isinstance(entry, dict):
        return False
    if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in ('model_slug', 'url', 'finding', 'pillar')):
        return False
    if entry['pillar'] not in PILLARS:
        return False
    parsed = urlparse(entry['url'])
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'https':
        return False
    if platform == 'youtube':
        if host not in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'):
            return False
        if entry.get('reviewer') not in REVIEWERS:
            return False
        if not approved_channels or entry.get('channel_id') != approved_channels.get(entry['reviewer']):
            return False
        return bool(entry.get('verified_from_content') is True)
    return host in ('reddit.com', 'www.reddit.com', 'old.reddit.com') and entry.get('verified_from_content') is True


def feedback_for_model(data, model_slug, approved_channels=None):
    output = {'youtube': [], 'reddit': []}
    for platform in output:
        for entry in data.get(platform, []):
            if entry.get('model_slug') == model_slug and validate_feedback(entry, platform, approved_channels):
                output[platform].append(entry)
    return output


def discover_youtube_reviews(api_key, channel_ids, model, max_results=5, session=None):
    """Metadata discovery only. YouTube Data API does NOT supply third-party transcripts."""
    if not api_key or not all(channel_ids.get(name) for name in REVIEWERS):
        return []
    import requests
    session = session or requests
    found = []
    for reviewer in REVIEWERS:
        cid = channel_ids[reviewer]
        response = session.get('https://www.googleapis.com/youtube/v3/search', params={
            'part': 'snippet', 'type': 'video', 'channelId': cid,
            'q': f'{model} review', 'maxResults': min(max(int(max_results), 1), 10),
            'key': api_key,
        }, timeout=12)
        response.raise_for_status()
        for item in response.json().get('items', []):
            snippet = item.get('snippet', {})
            video_id = item.get('id', {}).get('videoId')
            # Check returned channel ID; titles and display names are not trusted identifiers.
            if snippet.get('channelId') != cid or not re.fullmatch(r'[\w-]{11}', video_id or ''):
                continue
            found.append({'reviewer': reviewer, 'channel_id': cid, 'title': snippet.get('title', ''),
                          'published': snippet.get('publishedAt', ''),
                          'url': f'https://www.youtube.com/watch?v={video_id}',
                          'status': 'Discovery only — no review findings extracted'})
    return found
