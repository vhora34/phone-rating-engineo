"""Protocol-matched DXOMARK reference indicators, never independent /10 quality ratings.

A reference is an explicitly documented comparison anchor, NOT the theoretical
maximum DXOMARK score. No network requests or scraping are performed.
"""
from datetime import date

METRICS = {'camera', 'photo', 'video'}


def relative_indicator(raw_score, reference, metric, protocol):
    """Return a reproducible percentage of a fixed reference, or a refusal reason.

    The caller must supply reference provenance, a protocol, and a metric.
    A >100% result is valid: the device has surpassed the fixed anchor.
    """
    if metric not in METRICS:
        return {'available': False, 'reason': 'Unsupported DXOMARK metric'}
    if not isinstance(reference, dict):
        return {'available': False, 'reason': 'No documented reference configured'}
    if reference.get('metric') != metric or reference.get('protocol') != protocol:
        return {'available': False, 'reason': 'Reference metric or testing protocol mismatch'}
    if not reference.get('source_url') or not reference.get('as_of'):
        return {'available': False, 'reason': 'Reference provenance or date missing'}
    try:
        date.fromisoformat(reference['as_of'])
        raw = float(raw_score)
        best = float(reference['score'])
        if raw < 0 or best <= 0:
            raise ValueError
    except (ValueError, TypeError, KeyError):
        return {'available': False, 'reason': 'Invalid score, reference, or date'}
    return {
        'available': True,
        'raw_score': raw,
        'reference_score': best,
        'relative_percent': round(raw / best * 100, 1),
        'reference_as_of': reference['as_of'],
        'reference_source': reference['source_url'],
        'protocol': protocol,
        'metric': metric,
        'is_quality_rating': False,
    }


def reference_for(evidence, metric, protocol):
    return evidence.get('dxomark_references', {}).get(protocol, {}).get(metric)
