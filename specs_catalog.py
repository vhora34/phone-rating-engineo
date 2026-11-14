"""Read user-supplied smartphone specification CSVs; no external verification implied."""
import csv
import re
from pathlib import Path
from datetime import date

FILES = ('smartphones_2025_specs.csv', 'smartphones_2026_specs.csv')

def normalize(value):
    return re.sub(r'[^a-z0-9]+', '', str(value).casefold().replace('+', 'plus'))

def load_catalog():
    records = []
    for filename in FILES:
        path = Path(__file__).resolve().parent / filename
        if not path.exists():
            continue
        with path.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                row['_source_file'] = filename
                records.append(row)
    return records

def find_catalog_phone(query):
    wanted = normalize(query)
    if not wanted:
        return []
    matches = []
    for row in load_catalog():
        full = normalize(row['brand'] + ' ' + row['model'])
        model = normalize(row['model'])
        if wanted == full or wanted == model:
            matches.append(row)
    return matches

def is_future_release(row):
    try:
        return date.fromisoformat(row['release_month'] + '-01') > date.today().replace(day=1)
    except (ValueError, KeyError):
        return True
