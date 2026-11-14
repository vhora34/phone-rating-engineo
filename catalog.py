"""Canonical catalog and evidence-aware market cohort helpers."""
import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
BRACKETS = ((15000, 'Budget'), (30000, 'Mid-Range'), (50000, 'Upper Mid-Range'), (float('inf'), 'Flagship'))
VARIANT_RE = re.compile(r'(?i)(?:\b(?:ram|rom|storage)\s*[:=-]?\s*)?\b\d+\s*(?:gb|tb)\b(?:\s*(?:ram|rom|storage))?|\b\d+\s*(?:/|\+)\s*\d+\s*(?:gb|tb)?\b|\([^)]*\b(?:ram|storage|rom)\b[^)]*\)')

def slugify_model(brand, model):
    """Strip capacity variants, not model generations (e.g. Galaxy S25)."""
    raw = unicodedata.normalize('NFKD', str(model))
    raw = VARIANT_RE.sub(' ', raw)
    raw = re.sub(r'(?i)\b(?:5g|4g)\b', ' ', raw) if False else raw
    raw = re.sub(r'(?i)\b(?:ram|rom|storage)\b', ' ', raw)
    prefix = unicodedata.normalize('NFKD', str(brand)).strip()
    if raw.casefold().startswith(prefix.casefold() + ' '):
        raw = raw[len(prefix):].strip()
    value = f'{prefix} {raw}'.lower()
    value = re.sub(r'[^a-z0-9]+', '_', value).strip('_')
    return value

def price_bracket(price):
    try: price = float(price)
    except (TypeError, ValueError): return None
    if price <= 0: return None
    return next(name for upper, name in BRACKETS if price < upper)

def numbers(raw):
    return [int(v) for v in re.findall(r'\d+', str(raw or ''))]

def available_rams(phone):
    return sorted({n for n in numbers(phone['specs'].get('ram_gb')) if 2 <= n <= 32}) or [4, 6, 8, 12, 16]

def available_storages(phone):
    return sorted({n for n in numbers(phone['specs'].get('storage_gb')) if 32 <= n <= 2048}) or [64, 128, 256, 512]

def load_catalog(root=ROOT):
    root = Path(root)
    merged = {}
    for year in (2025, 2026):
        with (root / f'smartphones_{year}_specs.csv').open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                brand, model = row['brand'].strip(), row['model'].strip()
                slug = slugify_model(brand, model)
                merged[slug] = {'brand': brand, 'model': model, 'id': slug, 'status': 'CSV specs: not independently verified', 'specs': row,
                                'launch_price': float(row['launch_price_inr']) if row.get('launch_price_inr','').strip().replace('.','',1).isdigit() else None}
    with (root / 'historical_models_catalog.csv').open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            brand, model = row['brand'].strip(), row['model'].strip()
            slug = slugify_model(brand, model)
            merged.setdefault(slug, {'brand': brand, 'model': model, 'id': slug, 'status': 'Model name only; specifications unverified', 'specs': {}, 'launch_price': None})
    for phone in merged.values():
        phone['bracket'] = price_bracket(phone['launch_price'])
    return sorted(merged.values(), key=lambda r: (r['brand'].casefold(), r['model'].casefold()))

def bracket_averages(phones, ratings):
    """Only score real cohort members: ratings keyed by canonical slug, no guessed market average."""
    groups = {}
    for phone in phones:
        rating = ratings.get(phone['id'])
        bracket = phone.get('bracket')
        if bracket and rating is not None:
            groups.setdefault(bracket, []).append(float(rating))
    return {name: round(sum(values)/len(values), 2) for name, values in groups.items()}
