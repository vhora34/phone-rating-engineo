"""Streamlit UI for provisional evidence-first ratings."""
import streamlit as st
from catalog import load_catalog, available_rams, available_storages, price_bracket, bracket_averages
from scoring import load_evidence, rate_phone
from dxomark_relative import relative_indicator, reference_for
from owner_feedback import load_feedback, feedback_for_model, discover_youtube_reviews, REVIEWERS

st.set_page_config(page_title='Phone Rating Engine', page_icon='📱', layout='wide')
st.title('📱 Phone Rating Engine')
st.caption('Transparent 4-pillar estimates • Evidence tiers shown • India-market catalog')
st.warning('Scores inferred from component or raw specs are **provisional estimates**, not verified lab ratings. Market verdicts require a real comparable cohort.')

@st.cache_data
def get_catalog(): return load_catalog()

@st.cache_data
def get_evidence(): return load_evidence()

phones = get_catalog()
evidence = get_evidence()
brands = sorted({p['brand'] for p in phones}, key=str.casefold)
brand = st.selectbox('Brand', brands)
models = [p for p in phones if p['brand'] == brand]
phone = st.selectbox('Model', models, format_func=lambda p: p['model'])
cols = st.columns(3)
with cols[0]: ram = st.selectbox('RAM (GB)', available_rams(phone))
with cols[1]: storage = st.selectbox('Storage (GB)', available_storages(phone))
with cols[2]:
    default_price = int(phone.get('launch_price') or 0)
    price = st.number_input('Variant purchase price (₹)', min_value=0, max_value=1000000, value=default_price, step=500,
                            help='Enter actual price for this RAM/storage variant; CSV launch price is not variant-specific.')
if price > 250000: st.warning('Unusually high price. Check for an extra zero.')
if not phone['specs']: st.info('This catalog entry has a model name only. No verified specifications.')
else: st.caption('Specifications imported from user-provided CSV; not independently verified.')

# Peer averages require complete, source-linked model-level ratings. Exclude selected phone.
# Never treat raw-spec heuristics as verified market comparison data.
verified = {}
for p in phones:
    if p['id'] == phone['id'] or not p['specs']: continue
    r = rate_phone(p, evidence, available_rams(p)[0], available_storages(p)[0])
    if all(r['tiers'][pillar] == 1 for pillar in ('performance', 'camera', 'battery', 'display')) and r['overall_rating'] is not None:
        verified[p['id']] = r['overall_rating']
market = bracket_averages(phones, verified)
selected_bracket = price_bracket(price) or phone['bracket']
# Conservative minimum sample size for market verdict.
peer_count = sum(1 for p in phones if p['id'] in verified and p['bracket'] == selected_bracket)
avg = market.get(selected_bracket) if peer_count >= 3 else None
result = rate_phone(phone, evidence, ram, storage, variant_price=price or None, bracket_avg_rating=avg)
external = evidence.get('models', {}).get(phone['id'], {}).get('external_tests', {})
dxo = external.get('dxomark_camera')

st.subheader(f'{phone["brand"]} {phone["model"]} · {ram} GB / {storage} GB')
a, b, c, d = st.columns(4)
a.metric('Overall Rating /10', f'{result["overall_rating"]:.2f}' if result['overall_rating'] is not None else 'Not rated')
b.metric('Phone Category', result['category'])
c.metric('Value Verdict Tier', result['value_tag'])
d.metric('Evidence Confidence', result['confidence'])
st.info(f'**Variant verdict:** {result["verdict"]}')
if result['overall_rating'] is not None and any(t != 1 for t in result['tiers'].values()):
    st.caption('Overall rating is a provisional hardware proxy. It does not establish camera image quality, real battery endurance, or sustained gaming FPS.')
if avg is None: st.caption(f'Market comparison unavailable: {peer_count} fully model-verified comparable peers; at least 3 required. CSV launch prices are not verified current market prices.')
else: st.caption(f'Peer bracket: {selected_bracket} · verified peer mean: {avg:.2f}/10 · rating delta: {result["rating_delta"]:+.2f} · base-price markup: {result["storage_markup_pct"]}%')
st.subheader('Four pillars')
cols = st.columns(4)
for i, pillar in enumerate(('performance','camera','battery','display')):
    val = result['scores'][pillar]
    cols[i].metric(pillar.title(), f'{val:.2f}/10' if val is not None else 'Not rated')
    cols[i].caption({1:'Model evidence',2:'Component inference',3:'Spec-only estimate',None:'Missing'}[result['tiers'][pillar]])
with st.expander('Evidence & Audit Trail', expanded=True):
    for entry in result['audit_trail']:
        st.markdown(f'**{entry["pillar"].title()} — Tier {entry["tier"] or "missing"} — {entry["origin"]}**')
        st.write(entry['note'])
        for src in entry['sources']:
            st.markdown(f'[{src["title"]}]({src["url"]})')
    observations = evidence.get('models', {}).get(phone['id'], {}).get('observations', [])
    if observations:
        st.markdown('**Original external measurements (not converted to /10)**')
        for obs in observations:
            st.markdown(f"- **{obs['pillar'].title()} · {obs['source'].title()}**: {obs['metric']} = {obs['value']:g} {obs['unit']} · {obs['tested_on']} · [Original test]({obs['url']})")
            if obs.get('test_conditions'): st.caption(f"Conditions: {obs['test_conditions']}")
            if obs.get('notes'): st.caption(obs['notes'])
    if dxo:
        st.markdown('**Supplementary independent camera source (not converted to /10)**')
        st.write(f"DXOMARK Camera {dxo['raw_score']} · {dxo['protocol']} · {dxo['published']}")
        st.markdown(f"[Original test]({dxo['url']})")
    if not any(x['sources'] for x in result['audit_trail']):
        st.warning('No independent, source-linked evidence is currently available for this phone. All displayed numerical values are unverified spec estimates.')
# Independently sourced DXOMARK camera test, retained in original units.
if dxo:
    st.subheader('Independent camera testing · DXOMARK')
    st.metric('DXOMARK Camera (original scale)', str(dxo['raw_score']))
    st.caption(f"Protocol: {dxo['protocol']} · Published: {dxo['published']} · This is NOT a /10 score and is not mixed into the four-pillar rating.")
    for finding in dxo['findings']:
        st.markdown(f'- {finding}')
    st.markdown(f"[Read original DXOMARK camera test]({dxo['url']})")
    reference = reference_for(evidence, 'camera', dxo.get('protocol'))
    indicator = relative_indicator(dxo['raw_score'], reference, 'camera', dxo.get('protocol'))
    if indicator['available']:
        st.metric('DXOMARK score relative to fixed reference', f"{indicator['relative_percent']:.1f}%")
        st.caption(f"{dxo['raw_score']} / {indicator['reference_score']:g} reference points · {indicator['protocol']} · reference dated {indicator['reference_as_of']}. Not a /10 camera quality rating; can exceed 100%.")
        st.markdown(f"[Reference source]({indicator['reference_source']})")
    else:
        st.caption('Relative reference indicator unavailable: ' + indicator['reason'] + '. Raw DXOMARK score remains visible without invented normalization.')
else:
    st.caption('No manually verified DXOMARK camera test is linked for this exact model.')
with st.expander('Imported specifications'):
    st.json(phone['specs'] or {})
with st.expander('Scoring limitations and methodology'):
    st.write('Equal weights across four pillars. Model scores require source-linked evidence; chipset and camera-sensor scores are inferred, not phone-specific tests. Raw-spec scores are heuristics. Missing pillars remain unscored. The RAM/storage modifier is a small multitasking proxy, not a CPU speed boost.')
    st.write('Camera megapixels and battery capacity do not reliably predict camera quality or actual endurance. The methodology requires calibration and independently verified observations before purchase decisions.')
st.caption(f'{len(phones)} catalog models · {len(evidence["models"])} model evidence records · {peer_count} verified comparable peers')


st.subheader('Reviewer & owner feedback')
st.caption('YouTube is restricted to Gyan Therapy and GeekyRanjit. Reddit findings require source-linked manual verification. Neither changes lab scores automatically.')
channel_ids = {
    'Gyan Therapy': st.secrets.get('GYAN_THERAPY_CHANNEL_ID', ''),
    'GeekyRanjit': st.secrets.get('GEEKYRANJIT_CHANNEL_ID', ''),
}
feedback = feedback_for_model(load_feedback(), phone['id'], channel_ids)
for platform, title in [('youtube', 'Verified YouTube findings'), ('reddit', 'Verified Reddit owner findings')]:
    with st.expander(title, expanded=True):
        if not feedback[platform]:
            st.info('No independently checked findings for this exact model yet.')
        for entry in feedback[platform]:
            st.markdown(f"**{entry['pillar'].title()}** — {entry['finding']}")
            st.markdown(f"[Original source]({entry['url']})")
            if entry.get('reviewer'): st.caption(entry['reviewer'])
            if entry.get('published'): st.caption('Published: ' + entry['published'])
with st.expander('Discover reviews from the two approved YouTube channels'):
    if not st.secrets.get('YOUTUBE_API_KEY'):
        st.info('Add YOUTUBE_API_KEY to Streamlit Secrets to enable video discovery.')
    elif not all(channel_ids.values()):
        st.info('Add verified GYAN_THERAPY_CHANNEL_ID and GEEKYRANJIT_CHANNEL_ID to Streamlit Secrets. Channel names alone are not sufficient.')
    elif st.button('Find approved reviewer videos'):
        try:
            videos = discover_youtube_reviews(st.secrets['YOUTUBE_API_KEY'], channel_ids, f"{phone['brand']} {phone['model']}")
            if not videos: st.info('No matching videos found from the approved channels.')
            for video in videos:
                st.markdown(f"**{video['reviewer']}** · [{video['title']}]({video['url']})")
                st.caption(video['status'])
        except Exception as exc:
            st.error(f'Video lookup failed: {type(exc).__name__}. Check channel IDs, API quota and network access.')
