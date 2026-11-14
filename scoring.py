"""Three-tier provisional scoring; provenance and confidence always visible.

Tier-2 and Tier-3 scores are *inferences*, never independently measured quality.
Rubrics below are policy assumptions requiring calibration, especially camera.
"""
import json
import math
import re
from pathlib import Path
from catalog import slugify_model, price_bracket, available_rams, available_storages

PILLARS = ('performance', 'camera', 'battery', 'display')
CONFIDENCE = {1: 'High (Lab & Review Verified)', 2: 'Medium (Component + Spec Inferred)', 3: 'Low (Raw Specs Only)'}


def clamp(x): return round(max(0.0, min(10.0, float(x))), 2)
def scale(x, low, high): return clamp(2 + 8 * (float(x) - low) / (high - low))
def first_number(s):
    match = re.search(r'\d+(?:\.\d+)?', str(s or ''))
    return float(match.group()) if match else None

def load_evidence(path=None):
    path = Path(path) if path else Path(__file__).parent / 'evidence.json'
    try: data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError): return {'models': {}, 'components': {}}
    if not isinstance(data, dict): return {'models': {}, 'components': {}}
    return {'models': data.get('models', {}) if isinstance(data.get('models'), dict) else {},
            'components': data.get('components', {}) if isinstance(data.get('components'), dict) else {}}

def _spec_baseline(specs):
    """Transparent heuristic based only on available fields, not lab findings."""
    out, notes = {}, []
    ram = first_number(specs.get('ram_gb'))
    if ram is not None:
        out['performance'] = scale(ram, 3, 16)
        notes.append(f'Performance spec proxy: {ram:g} GB RAM (not CPU/GPU benchmark).')
    # Megapixels are a weak proxy; conservative narrow range, explicitly provisional.
    mp = first_number(specs.get('rear_camera'))
    if mp is not None:
        out['camera'] = clamp(4.0 + min(mp, 50) / 50 * 1.5)
        notes.append(f'Camera spec proxy: {mp:g} MP; megapixels cannot establish image quality.')
    mah = first_number(specs.get('battery_mah'))
    watts = first_number(specs.get('charging_w'))
    if mah is not None:
        out['battery'] = clamp(0.8 * scale(mah, 3000, 7000) + 0.2 * (scale(watts, 10, 120) if watts is not None else 5))
        notes.append(f'Battery spec proxy: {mah:g} mAh' + (f', {watts:g} W' if watts is not None else '') + '; endurance untested.')
    display = str(specs.get('display_type') or '')
    refresh = re.search(r'(\d{2,3})\s*hz', display, re.I)
    hz = float(refresh.group(1)) if refresh else None
    if hz is not None or display:
        panel = 1.0 if re.search(r'amoled|oled', display, re.I) else 0.0
        out['display'] = clamp((scale(hz, 60, 144) if hz else 5) * .75 + (6 + panel * 2) * .25)
        notes.append(f'Display spec proxy: {display}; no measured brightness/color accuracy.')
    return out, notes

def _component_entries(evidence, kind, key):
    group = evidence.get('components', {}).get(kind, {})
    if not isinstance(group, dict) or not key: return None
    for label, entry in group.items():
        if label.casefold().strip() == str(key).casefold().strip(): return entry
    return None

def _sensor_from_specs(specs):
    # A sensor ID cannot be safely inferred from '50MP + 12MP'; require explicit field.
    return specs.get('primary_camera_sensor') or specs.get('camera_sensor') or ''

def _record_score(record, pillar, origin, trail, tier):
    """Require source URLs for model-level verification; component provenance for Tier 2."""
    if not isinstance(record, dict): return None
    val = record.get('score')
    try:
        val = float(val)
        if not math.isfinite(val) or not 0 <= val <= 10: return None
    except (TypeError, ValueError): return None
    sources = record.get('sources') or []
    if not isinstance(sources, list): sources = []
    sources = [s for s in sources if isinstance(s, dict) and str(s.get('url', '')).startswith('https://') and s.get('title')]
    if not sources: return None
    trail.append({'pillar': pillar, 'tier': tier, 'origin': origin, 'note': record.get('note') or 'Evidence record', 'sources': sources})
    return round(val, 2)

def resolve_pillars(phone, evidence):
    specs = phone.get('specs') or {}
    slug = phone.get('id') or slugify_model(phone['brand'], phone['model'])
    baseline, notes = _spec_baseline(specs)
    scores, tiers, trail = {}, {}, []
    model_data = evidence.get('models', {}).get(slug, {})
    if not isinstance(model_data, dict): model_data = {}
    chipset = specs.get('processor') or specs.get('chipset')
    sensor = _sensor_from_specs(specs)
    for pillar in PILLARS:
        val = _record_score(model_data.get(pillar), pillar, f'Model: {slug}', trail, 1)
        if val is not None:
            scores[pillar], tiers[pillar] = val, 1
            continue
        kind, name = ('chipsets', chipset) if pillar == 'performance' else ('camera_sensors', sensor) if pillar == 'camera' else (None, None)
        component = _component_entries(evidence, kind, name) if kind else None
        val = _record_score(component.get(pillar) if isinstance(component, dict) else None, pillar, f'Component: {name}', trail, 2)
        if val is not None:
            scores[pillar], tiers[pillar] = val, 2
        elif pillar in baseline:
            scores[pillar], tiers[pillar] = baseline[pillar], 3
            trail.append({'pillar': pillar, 'tier': 3, 'origin': 'CSV specification heuristic', 'note': next((n for n in notes if n.lower().startswith(pillar.lower())), 'Raw spec proxy; not tested.'), 'sources': []})
        else:
            scores[pillar], tiers[pillar] = None, None
            trail.append({'pillar': pillar, 'tier': None, 'origin': 'Missing data', 'note': 'No usable evidence or specification for this pillar.', 'sources': []})
    return scores, tiers, trail

def classify_phone(scores, overall, bracket):
    present = {k: v for k, v in scores.items() if v is not None}
    if len(present) != 4 or overall is None: return 'Insufficient Data'
    mean = sum(present.values()) / 4
    highest = max(present, key=present.get)
    spread = max(present.values()) - min(present.values())
    tier = bracket or 'Unpriced'
    if spread <= .7 and overall >= 7.5:
        return 'Budget All-Rounder' if tier == 'Budget' else 'Balanced All-Rounder'
    names = {'performance': 'Gaming & Performance', 'camera': 'Camera-Centric', 'battery': 'Battery', 'display': 'Display'}
    if present[highest] - mean >= .8 or present[highest] > 8.5:
        suffix = {'performance': 'Beast', 'camera': 'Specialist', 'battery': 'Champion', 'display': 'Specialist'}[highest]
        if highest == 'camera': return f'{tier} Camera-Centric {suffix}'
        return f'{tier} {names[highest]} {suffix}'
    return f'{tier} All-Rounder' if spread <= 1.5 else f'{tier} Mixed Strengths'

def variant_modifier(ram, storage, bracket):
    """Small proxy for multitasking/storage longevity, NOT measured SoC uplift."""
    penalty = ram < 8 and bracket in ('Mid-Range', 'Upper Mid-Range', 'Flagship') or storage < 128
    modifier = (-.45 if ram < 8 and bracket in ('Mid-Range', 'Upper Mid-Range', 'Flagship') else 0) + (-.35 if storage < 128 else 0)
    if ram >= 8 and storage >= 256: modifier += .15
    if ram >= 12 and storage >= 256: modifier += .05
    return round(modifier, 2), bool(penalty)

def value_verdict(overall_rating, bracket_avg_rating, variant_price, base_model_price, bottleneck=False):
    if overall_rating is None or bracket_avg_rating is None:
        return {'value_tag': 'Insufficient Market Evidence', 'verdict': 'Comparable, evidence-scored phones are needed before a market-relative verdict.', 'rating_delta': None, 'storage_markup_pct': None}
    delta = round(overall_rating - bracket_avg_rating, 2)
    markup = round((variant_price - base_model_price) / base_model_price * 100, 2) if variant_price and base_model_price and base_model_price > 0 else None
    if bottleneck: tag, verdict = 'Bottlenecked Variant', 'This RAM/storage configuration is constrained for its price segment; consider a higher-capacity option.'
    elif delta >= .2 and markup is not None and markup > 20: tag, verdict = 'Great Phone, Overpriced Variant', 'The phone outperforms its market cohort, but this variant costs over 20% more than the base configuration; consider the base variant.'
    elif delta >= .5 and markup is not None and markup <= 15: tag, verdict = 'Category Killer / Best Value Variant', 'This configuration exceeds the comparable price-tier average with a modest markup over the base model.'
    elif delta <= -.5: tag, verdict = 'Overpriced for the Market', 'Its estimated rating trails similarly priced phones; compare alternatives before buying.'
    else: tag, verdict = 'Fair Market Value', 'This variant is broadly competitive within its price tier, subject to the stated evidence confidence.'
    return {'value_tag': tag, 'verdict': verdict, 'rating_delta': delta, 'storage_markup_pct': markup}

def rate_phone(phone, evidence, ram, storage, variant_price=None, bracket_avg_rating=None, base_model_price=None):
    scores, tiers, trail = resolve_pillars(phone, evidence)
    bracket = price_bracket(variant_price) or phone.get('bracket') or price_bracket(phone.get('launch_price'))
    modifier, bottleneck = variant_modifier(int(ram), int(storage), bracket)
    if scores['performance'] is not None:
        scores['performance'] = clamp(scores['performance'] + modifier)
        trail.append({'pillar': 'performance', 'tier': 3, 'origin': 'Variant heuristic', 'note': f'{ram} GB RAM / {storage} GB storage; {modifier:+.2f} performance/multitasking proxy (not measured CPU gain).', 'sources': []})
    overall = round(sum(scores.values()) / 4, 2) if all(v is not None for v in scores.values()) else None
    worst_tier = max((t for t in tiers.values() if t is not None), default=3)
    if any(t is None for t in tiers.values()): worst_tier = 3
    value = value_verdict(overall, bracket_avg_rating, variant_price, base_model_price or phone.get('launch_price'), bottleneck)
    return {'scores': scores, 'overall_rating': overall, 'category': classify_phone(scores, overall, bracket),
            'confidence': CONFIDENCE[worst_tier], 'tiers': tiers, 'audit_trail': trail, 'bracket': bracket,
            'variant_modifier': modifier, 'bottleneck': bottleneck, **value}
