import streamlit as st
from engine import PHONES, CATEGORIES, LABELS, scores_for, rating_word, find_phone
from lookup import find_specs, extract_attributes, estimate_scores
from evidence import load_evidence, evidence_for, summarize
from ownership import profiles, capacity_scenarios
from youtube_reviews import find_review_videos, get_public_comments, YouTubeError
from source_lookup import source_page, search_links, model_tokens_present
from specs_catalog import find_catalog_phone, is_future_release
from historical_catalog import find_historical_models

st.set_page_config(page_title='Phone Rating Engine v5', page_icon='📱', layout='wide')
st.title('📱 Phone Rating Engine v5')
st.caption('Hardware ratings + buyer fit + battery ageing scenarios + source-linked real-world reviews. Estimates are labelled; missing evidence is never invented.')

@st.cache_data(ttl=604800, show_spinner=False)
def youtube_search_cached(model, api_key):
    return find_review_videos(model, api_key)

@st.cache_data(ttl=604800, show_spinner=False)
def youtube_comments_cached(video_id, api_key):
    return get_public_comments(video_id, api_key)

@st.cache_data(ttl=86400, show_spinner=False)
def lookup(model):
    return find_specs(model)

with st.form('analyze'):
    model = st.text_input('Phone model', placeholder='Samsung Galaxy S25', value='Samsung Galaxy S25')
    a, b, c = st.columns(3)
    ram = a.selectbox('RAM (GB)', [4, 6, 8, 12, 16, 24], index=3)
    storage = b.selectbox('Storage (GB)', [64, 128, 256, 512, 1024], index=2)
    price = c.number_input('Price in ₹ (0 = unknown)', min_value=0, max_value=500000, step=500)
    submitted = st.form_submit_button('Analyze phone', type='primary', use_container_width=True)

if submitted:
    if not model.strip():
        st.error('Enter a phone model.')
        st.stop()
    phone, suggestions = find_phone(model)
    if phone:
        st.subheader(f'{phone.name} · {ram}GB / {storage}GB')
        if (ram, storage) != (phone.ram, phone.storage):
            st.warning('This RAM/storage combination has not been checked against official available variants.')
        scores, overall, fits, _, _, used_price = scores_for(phone, ram, storage, price or None)
        x, y, z = st.columns(3)
        x.metric('Editorial overall rating', f'{overall:.1f}/10')
        y.metric('Verdict', rating_word(overall))
        z.metric('Price used', f'₹{used_price:,.0f}')
        if not price:
            st.warning('Value score uses an illustrative reference price. Enter your actual price for a meaningful value assessment.')
        st.info('These are manually assigned editorial scores, not independently validated benchmarks. The gaming score is only a proxy: no sustained FPS, thermals or GPU tests are included.')
        tab1, tab2, tab3, tab4 = st.tabs(['Scores & buyer fit', '5-year ownership', 'Reviews & sources', 'Specs & verdict'])
        with tab1:
            left, right = st.columns(2)
            with left:
                st.markdown('#### Category ratings')
                for k in CATEGORIES:
                    st.write(f'**{LABELS[k]}** — {scores[k]:.1f}/10')
                    st.progress(scores[k]/10)
            with right:
                st.markdown('#### Buyer profiles')
                for name, value in profiles(scores):
                    st.write(f'{name}: **{value:.1f}/10**')
                    st.progress(value/10)
                st.caption('Buyer-profile scores use transparent weights; gaming is a proxy until verified gaming tests are added.')
        with tab2:
            st.markdown('#### Battery capacity scenarios (not a battery-health prediction)')
            st.line_chart(capacity_scenarios(), x='Year')
            st.caption('3%, 6% and 10% annual capacity loss are illustrative scenarios, not measured deterioration for this phone. Heat, charging, usage and cell chemistry matter. A battery replacement may be worthwhile during 5-year ownership.')
            st.markdown('#### Processor longevity')
            st.write('Processor ageing cannot be reliably predicted from chipset branding alone. Sustained benchmark tests, efficiency, RAM/storage and software updates are needed.')
            st.write('**Existing editorial longevity score:**', f"{scores['longevity']:.1f}/10")
            st.caption('This is not a forecast of future gaming FPS or the probability of hardware failure.')
        with tab3:
            records, warnings = load_evidence()
            for w in warnings:
                st.warning(w)
            matching = evidence_for(phone.name, records)
            summary = summarize(matching)
            st.write(f"**Evidence coverage:** {summary['confidence']}")
            st.write(f"**Source-linked entries:** {summary['count']}")
            if summary['issues']:
                st.write('**Negative mentions by topic (not failure rates):**', summary['issues'])
            if not matching:
                st.info('No reviewed, source-linked evidence has been added for this model. Reddit/YouTube/retailer sentiment has NOT been analyzed. No owner score or reliability claim is generated.')
            for r in sorted(matching, key=lambda x: x['date'], reverse=True):
                st.markdown(f"**{r['source_type'].replace('_',' ').title()}** · {r['date']} · {r['topic']} · {r['sentiment']}")
                st.write(r['summary'])
                st.link_button('View original source', r['url'])
            st.caption('Curated evidence entries must be checked by the project maintainer. Multiple posts may describe the same incident; complaints cannot establish failure rates. No reviews are scraped automatically.')
            st.markdown('#### YouTube review discovery (live API)')
            st.caption('Search uses your private API key. Results are metadata, not verified review findings or endorsements. Search costs about 100 quota units; results are cached for 7 days.')
            youtube_key = st.secrets.get('YOUTUBE_API_KEY', '')
            if not youtube_key:
                st.warning('Add YOUTUBE_API_KEY to Streamlit Community Cloud → App settings → Secrets to enable live YouTube results.')
            elif st.button('Find YouTube reviews', key='youtube_find'):
                try:
                    st.session_state['youtube_videos'] = youtube_search_cached(phone.name, youtube_key)
                    st.session_state['youtube_model'] = phone.name
                except YouTubeError as exc:
                    st.error(str(exc))
            if st.session_state.get('youtube_model') == phone.name:
                for video in st.session_state.get('youtube_videos', []):
                    st.markdown(f"**{video['title']}**")
                    st.caption(f"{video['channel']} · {video['published']}")
                    st.link_button('Watch original video', video['url'])
                    with st.expander('Public comments (not representative)'):
                        if st.button('Load public comments', key='comments_' + video['video_id']):
                            try:
                                comments = youtube_comments_cached(video['video_id'], youtube_key)
                                if not comments:
                                    st.info('No accessible public comments.')
                                for comment in comments:
                                    st.write(comment['text'])
                                    st.caption(f"{comment['published']} · {comment['likes']} likes")
                            except YouTubeError as exc:
                                st.warning(str(exc))
                st.info('Comments are unverified opinions, can contain spam, and do not establish defect rates. No automated sentiment score is calculated.')
            st.markdown('#### Find external discussions (not yet analyzed)')
            from urllib.parse import quote_plus
            st.link_button('Search Reddit', 'https://www.reddit.com/search/?q=' + quote_plus(phone.name + ' review problems'))
            st.link_button('Search YouTube', 'https://www.youtube.com/results?search_query=' + quote_plus(phone.name + ' long term review'))
            st.link_button('Search Google reviews', 'https://www.google.com/search?q=' + quote_plus(phone.name + ' owner reviews'))
        with tab4:
            for fact in phone.facts:
                st.write('•', fact)
            left, right = st.columns(2)
            with left:
                st.markdown('#### Strengths')
                for item in phone.strengths:
                    st.write('✅', item)
            with right:
                st.markdown('#### Weaknesses')
                for item in phone.weaknesses:
                    st.write('⚠️', item)
            if phone.note:
                st.info(phone.note)
            st.write(f"**Most suitable buyer (by profile weights):** {profiles(scores)[0][0]}")
            st.caption('Specs are curated descriptions; verify regional variants and software commitments with manufacturer sources before purchasing.')
    else:
        catalog_matches = find_catalog_phone(model)
        if catalog_matches:
            st.subheader('Supplied specification catalog')
            st.info('These specifications come from uploaded CSV files. They have not been independently verified and do not establish camera quality, gaming FPS, reliability or long-term battery health.')
            if len(catalog_matches) > 1:
                st.warning('Multiple catalog records match this phone. They may describe different releases or contain conflicting specifications; compare before relying on them.')
            for row in catalog_matches:
                with st.expander(f"{row['brand']} {row['model']} · {row['_source_file']}", expanded=True):
                    if is_future_release(row):
                        st.warning('The listed release month is in the future. Treat these specifications as unconfirmed until verified against official announcements.')
                    for label, key in [('Listed release month','release_month'), ('Operating system','os'), ('Processor','processor'), ('RAM variants (GB)','ram_gb'), ('Storage variants (GB)','storage_gb'), ('Display size (inches)','display_size_in'), ('Display','display_type'), ('Rear cameras','rear_camera'), ('Front camera','front_camera'), ('Battery capacity (mAh)','battery_mah'), ('Charging','charging_w'), ('Listed launch price (INR)','launch_price_inr')]:
                        st.write(f"**{label}:** {row.get(key) or 'Not provided'}")
                    st.caption('The listed launch price is not a current market price. RAM/storage options must be confirmed for your region. No full score is generated from this CSV alone.')
        else:
            historical_matches = find_historical_models(model)
            if historical_matches:
                st.subheader('Historical model-name catalog')
                st.warning('These are model-name matches only, NOT verified specifications or ratings. Confirm the exact regional model before buying.')
                for candidate in historical_matches:
                    st.write(f"• {candidate['full_name']} — specifications not yet verified")
            else:
                st.info('No exact match in the uploaded specification catalog. Checking Wikipedia or an official manufacturer page.')
        st.info('Searching Wikipedia; if unavailable, use a verified manufacturer page.')
        try:
            result = lookup(model)
        except Exception as exc:
            st.warning(f'Wikipedia lookup unavailable: {exc}')
            result = None
        if not result:
            st.warning('No confident Wikipedia match. This does not mean the phone does not exist.')
            if suggestions:
                st.write('Similar curated names:', ', '.join(suggestions))
        st.markdown('#### Discover trustworthy specifications')
        for label, url in search_links(model).items():
            st.link_button(label, url)
        source_url = st.text_input('Optional: paste the official manufacturer specification page URL', key='manufacturer_url', placeholder='https://www.brand.com/...')
        if source_url:
            if st.button('Read specification page', key='read_specs'):
                try:
                    st.session_state['source_result'] = source_page(source_url)
                    st.session_state['source_model'] = model
                except Exception as exc:
                    st.error(f'Could not read page: {exc}')
        if st.session_state.get('source_model') == model and st.session_state.get('source_result'):
            result = st.session_state['source_result']
            if not model_tokens_present(model, result['title'] + ' ' + result['text'][:6000]):
                st.error('Model name not clearly found on source page. Verify the exact model and variant; no score is inferred.')
                result = None
        if result:
            st.subheader('Source: ' + result['title'])
            st.link_button('Open source and confirm exact variant', result['url'])
            st.warning('Source-derived specifications are unverified until you confirm the exact model and regional variant. Ratings below are partial heuristics, not measured tests.')
            attrs = extract_attributes(result)
            for label, key in [('Chipset','chipset'),('Battery capacity (mAh)','battery_mah'),('Display','display'),('Camera hardware','camera'),('Weight','weight'),('OS','os')]:
                if attrs[key]:
                    st.write(f'**{label}:** {attrs[key]}')
            partial = estimate_scores(attrs, ram, storage, price or None)
            for k in CATEGORIES:
                st.write(f'**{LABELS[k]}:** ' + (f'{partial[k]:.1f}/10 (rough heuristic)' if partial[k] is not None else 'Insufficient evidence'))
            st.info('No full overall score is generated for an unverified model. Battery capacity is not measured endurance, and chipset tiers are not sustained-performance benchmarks.')
        st.markdown('#### Live YouTube review discovery for this model')
        youtube_key = st.secrets.get('YOUTUBE_API_KEY', '')
        if not youtube_key:
            st.warning('Set YOUTUBE_API_KEY in Streamlit Secrets to enable live video search.')
        elif st.button('Find YouTube reviews', key='unknown_youtube'):
            try:
                st.session_state['unknown_videos'] = youtube_search_cached(model, youtube_key)
                st.session_state['unknown_video_model'] = model
            except YouTubeError as exc:
                st.error(str(exc))
        if st.session_state.get('unknown_video_model') == model:
            videos = st.session_state.get('unknown_videos', [])
            if not videos:
                st.info('No videos returned for this search.')
            for video in videos:
                st.markdown('**' + video['title'] + '**')
                st.caption(video['channel'] + ' · ' + video['published'])
                st.link_button('Watch review', video['url'])
            st.caption('Video listings are discovery results, not verified reviews or scored sentiment.')

st.divider()
with st.expander('How to add phones and real-world review evidence'):
    st.markdown('''**Phones:** Edit `PHONES` in `engine.py` and commit to GitHub.\n\n**Reviews:** Edit `reviews.json`. Add one entry per independently checked source with fields `model`, `source_type`, `url`, `date` (YYYY-MM-DD), `topic`, `sentiment`, `summary`. Accepted types: `reddit`, `youtube`, `retailer`, `independent_review`, `manufacturer`. No reviews are automatically collected.\n\nExample JSON:\n```json\n[\n  {\n    "model": "Samsung Galaxy S25",\n    "source_type": "youtube",\n    "url": "https://www.youtube.com/watch?v=REPLACE_WITH_REAL_VIDEO",\n    "date": "2026-11-01",\n    "topic": "battery",\n    "sentiment": "mixed",\n    "summary": "Replace this placeholder with your own verified summary of a real review."\n  }\n]\n```\nNever add example entries as if they were genuine evidence. The file ships empty.''')
