"""Source-assisted model discovery, without pretending to have a universal phone database."""
import json
import re
from urllib.parse import urlparse, quote_plus
import requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; PhoneRatingEngine/4.0; research prototype)'}
ALLOWED = ('http', 'https')

def search_links(model):
    q = quote_plus(model.strip())
    return {
        'Manufacturer specification search': 'https://www.google.com/search?q=' + quote_plus(model + ' official specifications smartphone'),
        'Independent review search': 'https://www.google.com/search?q=' + quote_plus(model + ' smartphone review battery chipset camera'),
        'YouTube review search': 'https://www.youtube.com/results?search_query=' + quote_plus(model + ' review gaming camera'),
        'Reddit owner search': 'https://www.reddit.com/search/?q=' + quote_plus(model + ' phone review'),
    }

def source_page(url):
    """Read a user-supplied public spec page, not an arbitrary internal endpoint."""
    from ipaddress import ip_address
    from socket import getaddrinfo
    parsed = urlparse(url.strip())
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Enter a public HTTPS manufacturer/product page URL.')
    host = parsed.hostname.lower()
    if host in ('localhost',) or host.endswith(('.local', '.internal')):
        raise ValueError('Local/private hosts are not allowed.')
    try:
        addresses = getaddrinfo(host, 443)
        if any(not ip_address(info[4][0]).is_global for info in addresses):
            raise ValueError('Private network addresses are not allowed.')
    except OSError as exc:
        raise ValueError('Cannot resolve this host.') from exc
    response = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=False)
    if 300 <= response.status_code < 400:
        raise ValueError('Redirecting page. Open its final HTTPS URL and paste that instead.')
    response.raise_for_status()
    if len(response.content) > 1_500_000:
        raise ValueError('Page is too large to inspect.')
    if 'html' not in response.headers.get('content-type', '').lower():
        raise ValueError('This URL did not return an HTML page.')
    soup = BeautifulSoup(response.text, 'html.parser')
    for tag in soup(['script','style','nav','footer','header']):
        tag.decompose()
    title = soup.title.get_text(' ', strip=True) if soup.title else host
    facts = []
    for row in soup.select('tr')[:200]:
        cells = row.find_all(['th','td'])
        if len(cells) >= 2:
            key = cells[0].get_text(' ', strip=True)[:70]
            value = cells[1].get_text(' ', strip=True)[:250]
            if key and value and len(value) > 1:
                facts.append((key, value))
    text = soup.get_text(' ', strip=True)[:35000]
    return {'title':title[:200], 'url':url, 'fields': dict(facts), 'text':text, 'source':'User-provided source; model identity not verified'}

def model_tokens_present(model, text):
    # Explicit confirmation is always required; this only raises mismatch warnings.
    words = re.findall(r'[a-z0-9]+', model.lower())
    body = re.sub(r'[^a-z0-9]+', ' ', text.lower())
    return len(words) >= 2 and all(re.search(r'\b'+re.escape(w)+r'\b', body) for w in words if len(w)>1)
