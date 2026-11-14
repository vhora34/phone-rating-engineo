"""Transparent scenario modelling, not a forecast of device failure."""
from datetime import date

WEIGHTS = {
    'All-rounder': {'basic': .20, 'camera': .20, 'battery': .20, 'longevity': .20, 'build': .10, 'design': .10},
    'Camera-centric': {'camera': .50, 'basic': .10, 'battery': .10, 'longevity': .15, 'build': .10, 'design': .05},
    'Gaming-centric (proxy)': {'basic': .40, 'battery': .20, 'longevity': .20, 'build': .10, 'design': .10},
    'Long-term keeper': {'longevity': .40, 'basic': .25, 'battery': .15, 'build': .15, 'camera': .05},
    'Battery-focused': {'battery': .50, 'longevity': .20, 'basic': .15, 'build': .10, 'design': .05},
}

def profiles(scores):
    return sorted(((name, sum(scores[k] * w for k, w in weights.items())) for name, weights in WEIGHTS.items()), key=lambda x: x[1], reverse=True)

def capacity_scenarios(years=5, annual_losses=(.03, .06, .10)):
    return [{'Year': year, **{f'{round(rate*100)}% annual loss': round(100 * (1-rate)**year, 1) for rate in annual_losses}} for year in range(years + 1)]
