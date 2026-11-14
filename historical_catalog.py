"""Model-name discovery only. No claims of specs, release dates or ratings."""
import csv
from pathlib import Path
from difflib import get_close_matches
from specs_catalog import normalize

FILE = Path(__file__).resolve().parent / 'historical_models_catalog.csv'

def find_historical_models(query, limit=5):
    if not FILE.exists() or not normalize(query):
        return []
    with FILE.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    wanted = normalize(query)
    exact = [r for r in rows if wanted == normalize(r['full_name'])]
    if exact:
        return exact[:limit]
    by_name = {normalize(r['full_name']): r for r in rows}
    keys = get_close_matches(wanted, list(by_name), n=limit, cutoff=0.84)
    return [by_name[k] for k in keys]
