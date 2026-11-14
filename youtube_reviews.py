"""Public YouTube review discovery. No transcript or sentiment inference."""
import requests

BASE = 'https://www.googleapis.com/youtube/v3'

class YouTubeError(Exception):
    pass

def _get(endpoint, params):
    try:
        response = requests.get(f'{BASE}/{endpoint}', params=params, timeout=15)
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise YouTubeError(f'YouTube request failed: {exc}') from exc
    if response.status_code != 200:
        detail = payload.get('error', {}).get('message', 'Unknown API error')
        raise YouTubeError(f'YouTube API error ({response.status_code}): {detail}')
    return payload

def find_review_videos(model, api_key, max_results=6):
    """Search costs 100 quota units per call; cache caller-side."""
    if not api_key:
        raise YouTubeError('Missing YouTube API key in Streamlit Secrets.')
    result = _get('search', {
        'part': 'snippet', 'q': f'{model} long term review battery camera gaming',
        'type': 'video', 'maxResults': max_results, 'order': 'relevance',
        'key': api_key, 'safeSearch': 'moderate',
    })
    videos = []
    for item in result.get('items', []):
        video_id = item.get('id', {}).get('videoId')
        snippet = item.get('snippet', {})
        if not video_id:
            continue
        videos.append({
            'title': snippet.get('title', ''),
            'channel': snippet.get('channelTitle', ''),
            'published': snippet.get('publishedAt', '')[:10],
            'description': snippet.get('description', ''),
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'video_id': video_id,
        })
    return videos

def get_public_comments(video_id, api_key, max_results=20):
    """Returns top-level public comments only; not a representative sample."""
    result = _get('commentThreads', {
        'part': 'snippet', 'videoId': video_id, 'maxResults': max_results,
        'order': 'relevance', 'textFormat': 'plainText', 'key': api_key,
    })
    comments = []
    for item in result.get('items', []):
        top = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
        if top.get('textDisplay'):
            comments.append({'text': top['textDisplay'], 'likes': top.get('likeCount', 0),
                             'published': top.get('publishedAt', '')[:10]})
    return comments
