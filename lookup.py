"""Best-effort free Wikipedia specification lookup; no API key.
Not all phones have a dedicated article. Never silently substitute a model.
"""
import re
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

API = 'https://en.wikipedia.org/w/api.php'
HEADERS = {'User-Agent': 'PhoneRatingEngineDemo/1.0 (educational app; contact via repository)'}


def _request(params):
    response = requests.get(API, params=params, headers=HEADERS, timeout=12)
    response.raise_for_status()
    data = response.json()
    if 'error' in data:
        raise ValueError(data['error'].get('info', 'Wikipedia request failed'))
    return data


def _norm(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def find_specs(model):
    """Returns title, source URL, fields, evidence, or None. Never guess a match."""
    query = model.strip()
    if len(query) < 4:
        return None
    data = _request({'action': 'query', 'list': 'search', 'srsearch': f'intitle:"{query}" smartphone', 'srlimit': 8, 'format': 'json'})
    results = data.get('query', {}).get('search', [])
    if not results:
        data = _request({'action': 'query', 'list': 'search', 'srsearch': query, 'srlimit': 8, 'format': 'json'})
        results = data.get('query', {}).get('search', [])
    wanted = _norm(query)
    options = []
    for item in results:
        title = item['title']
        actual = _norm(title)
        score = SequenceMatcher(None, wanted, actual).ratio()
        # Reject S25 FE matching S25, etc.; exact token containment only if not an extra model suffix.
        if actual == wanted or score >= .89 and (wanted in actual or actual in wanted):
            options.append((score, title))
    if not options:
        return None
    title = sorted(options, reverse=True)[0][1]
    parsed = _request({'action': 'parse', 'page': title, 'prop': 'text', 'format': 'json', 'formatversion': 2})
    html = parsed.get('parse', {}).get('text', '')
    soup = BeautifulSoup(html, 'html.parser')
    fields = {}
    table = soup.select_one('table.infobox')
    if table:
        for tr in table.select('tr'):
            header = tr.find('th')
            cell = tr.find('td')
            if header and cell:
                key = ' '.join(header.stripped_strings).lower()
                value = ' '.join(cell.stripped_strings)
                value = re.sub(r'\[\d+\]', '', value)
                if key and value:
                    fields[key] = value[:450]
    for tag in soup(['sup', 'style', 'script']):
        tag.decompose()
    text = ' '.join(soup.stripped_strings)[:15000]
    return {'title': title, 'url': 'https://en.wikipedia.org/wiki/' + title.replace(' ', '_'),
            'fields': fields, 'text': text, 'source': 'Wikipedia (community-edited; verify with manufacturer)'}


def extract_attributes(result):
    """Conservative evidence extraction. Missing facts stay missing."""
    fields = result['fields']
    def field(*names):
        return ' '.join(v for k, v in fields.items() if any(n in k for n in names))
    chip = field('soc', 'chipset', 'processor', 'system on chip')
    battery = field('battery')
    display = field('display')
    camera = field('camera')
    weight = field('mass', 'weight')
    os = field('operating system')
    raw = result['text']
    if not chip:
        match = re.search(r'(Snapdragon\s+[\w +\-]{2,28}|Dimensity\s+\d{3,4}[\w +\-]*|Exynos\s+\d{3,4}|Apple\s+A\d{2}\s*Pro?)', raw, re.I)
        chip = match.group(0) if match else ''
    battery_match = re.search(r'(\d[\d,]{3,5})\s*mAh', battery, re.I)
    if not battery_match:
        battery_match = re.search(r'(\d[\d,]{3,5})\s*mAh', raw, re.I)
    capacity = int(battery_match.group(1).replace(',', '')) if battery_match else None
    if capacity and not 2000 <= capacity <= 15000:
        capacity = None
    return {'chipset': chip[:120], 'battery_mah': capacity, 'display': display[:200],
            'camera': camera[:200], 'weight': weight[:120], 'os': os[:120],
            'field_count': sum(bool(x) for x in (chip, capacity, display, camera, weight, os))}


def estimate_scores(attrs, ram, storage, price):
    """Only score dimensions with enough evidence. None means insufficient evidence.
    Ratings are rough heuristics, not objective performance or camera testing.
    """
    chip = attrs['chipset'].lower()
    chipset_score = None
    if re.search(r'snapdragon\s+8\s*(elite|gen\s*[234])|dimensity\s*9\d{3}|apple\s+a1[7-9]|apple\s+a2\d', chip):
        chipset_score = 9.3
    elif re.search(r'snapdragon\s+7\s*(\+|gen|s\s*gen)|dimensity\s*[78]\d{3}|exynos\s*\d{4}', chip):
        chipset_score = 7.8
    elif re.search(r'snapdragon\s+[46]|dimensity\s*6\d{3}', chip):
        chipset_score = 6.6
    # Unknown processor is not assigned a score.
    basic = min(10, chipset_score + min(.5, (ram - 8) * .08)) if chipset_score else None
    capacity = attrs['battery_mah']
    battery = max(5, min(9.6, 6.3 + (capacity - 4000) / 1150)) if capacity else None
    # Do not infer camera quality, build or software support from marketing specs.
    longevity = min(9.2, basic - .35 + (.2 if storage >= 256 else 0)) if basic else None
    scores = {'build': None, 'camera': None, 'design': None,
              'battery': battery, 'longevity': longevity, 'basic': basic, 'value': None}
    known = [v for v in (battery, longevity, basic) if v is not None]
    if len(known) >= 2 and price:
        scores['value'] = max(1, min(10, sum(known) / len(known) - (price - 30000) / 10000 * .7))
    return scores
