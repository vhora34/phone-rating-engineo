"""Curated, provenance-preserving external test import. No scraping or invented scores.

Usage: python evidence_pipeline.py validate
       python evidence_pipeline.py import observations.csv
CSV schema documented in EVIDENCE_PIPELINE.md.
"""
import csv
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from catalog import slugify_model

ROOT = Path(__file__).resolve().parent
PILLARS = {'performance', 'camera', 'battery', 'display'}
SOURCES = {'dxomark', 'phonearena', 'nanoreview', 'geekbench', '3dmark', 'notebookcheck', 'gsmarena', 'official', 'other'}


def validate_observation(row):
    errors = []
    for field in ('brand', 'model', 'pillar', 'source', 'metric', 'value', 'unit', 'url', 'tested_on'):
        if not str(row.get(field, '')).strip(): errors.append(f'missing {field}')
    pillar = str(row.get('pillar', '')).strip().lower()
    source = str(row.get('source', '')).strip().lower()
    if pillar not in PILLARS: errors.append('invalid pillar')
    if source not in SOURCES: errors.append('invalid source')
    try:
        number = float(row.get('value', ''))
        if not math.isfinite(number) or number < 0: errors.append('value must be finite and nonnegative')
    except (TypeError, ValueError): errors.append('value must be numeric')
    url = str(row.get('url', '')).strip()
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.netloc: errors.append('source must have an https URL')
    try: date.fromisoformat(str(row.get('tested_on', '')).strip())
    except ValueError: errors.append('tested_on must be YYYY-MM-DD')
    # Do not accept a converted /10 score as a measured raw result.
    if str(row.get('metric', '')).strip().lower() in {'score_out_of_10', 'our_score'}:
        errors.append('raw measurements only; /10 conversion requires separately calibrated rubric')
    return errors


def import_rows(data, rows):
    """Return updated copy and import summary. Existing manual pillar scores untouched."""
    data = json.loads(json.dumps(data))
    models = data.setdefault('models', {})
    accepted, rejected, duplicates = 0, [], 0
    for line, row in enumerate(rows, start=2):
        errors = validate_observation(row)
        if errors:
            rejected.append({'line': line, 'errors': errors})
            continue
        slug = slugify_model(row['brand'], row['model'])
        model = models.setdefault(slug, {'brand': row['brand'], 'model': row['model']})
        observations = model.setdefault('observations', [])
        observation = {k: str(row.get(k, '')).strip() for k in ('pillar', 'source', 'metric', 'value', 'unit', 'url', 'tested_on', 'variant', 'test_conditions', 'notes')}
        observation['pillar'] = observation['pillar'].lower()
        observation['source'] = observation['source'].lower()
        observation['value'] = float(observation['value'])
        identity = (observation['source'], observation['metric'], observation['url'], observation['variant'], observation['tested_on'])
        if any((o.get('source'), o.get('metric'), o.get('url'), o.get('variant'), o.get('tested_on')) == identity for o in observations):
            duplicates += 1
            continue
        observations.append(observation)
        accepted += 1
    return data, {'accepted': accepted, 'duplicates': duplicates, 'rejected': rejected}


def validate_database(data):
    errors = []
    for slug, model in data.get('models', {}).items():
        for i, observation in enumerate(model.get('observations', [])):
            row = {'brand': model.get('brand'), 'model': model.get('model'), **observation}
            problems = validate_observation(row)
            if problems: errors.append({'model': slug, 'index': i, 'errors': problems})
    return errors


def main(argv):
    path = ROOT / 'evidence.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if len(argv) == 2 and argv[1] == 'validate':
        errors = validate_database(data)
        print(json.dumps({'valid': not errors, 'errors': errors}, indent=2))
        return 1 if errors else 0
    if len(argv) != 3 or argv[1] != 'import':
        print('Usage: python evidence_pipeline.py validate | import observations.csv')
        return 2
    with open(argv[2], newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    updated, summary = import_rows(data, rows)
    print(json.dumps(summary, indent=2))
    if summary['rejected']:
        print('No changes written because some rows were invalid.')
        return 1
    path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
