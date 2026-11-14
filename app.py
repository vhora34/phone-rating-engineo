import streamlit as st
from engine import PHONES, CATEGORIES, LABELS, PROFILES, scores_for, rating_word

st.set_page_config(page_title='Phone Rating Engine', page_icon='📱', layout='wide')
st.title('📱 Phone Rating Engine')
st.caption('India-focused, offline editorial ratings • No account or API key required')
st.info('Ratings are subjective estimates, not laboratory measurements. Reference prices are illustrative, not live quotes. Confirm specifications, availability and the exact variant before buying.')

names = [p.name for p in PHONES]
with st.form('phone_form'):
    model = st.selectbox('Phone model', names, index=names.index('Samsung Galaxy S25'))
    phone = next(p for p in PHONES if p.name == model)
    a,b,c = st.columns(3)
    with a: ram = st.selectbox('RAM (GB)', [4,6,8,12,16,24], index=[4,6,8,12,16,24].index(phone.ram) if phone.ram in [4,6,8,12,16,24] else 2)
    with b: storage = st.selectbox('Storage (GB)', [64,128,256,512,1024], index=[64,128,256,512,1024].index(phone.storage))
    with c: price = st.number_input('Your purchase price (₹)', min_value=1000, max_value=500000, value=phone.reference_price, step=500)
    run = st.form_submit_button('Analyze phone', type='primary', use_container_width=True)

# Refresh defaults when changing the selected phone: Streamlit form widgets retain values
# intentionally, so the app warns if a variant differs from its reference configuration.
if run:
    if ram != phone.ram or storage != phone.storage:
        st.warning('This RAM/storage combination is user-selected and has NOT been verified as an officially sold variant. Confirm it exists before buying.')
    try:
        scores, overall, fits, ram, storage, price = scores_for(phone, ram, storage, price)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.divider()
    st.subheader(f'{phone.name} · {ram}GB / {storage}GB')
    x,y,z = st.columns(3)
    x.metric('Overall rating', f'{overall:.1f}/10')
    y.metric('Verdict', rating_word(overall))
    z.metric('Your price', f'₹{price:,.0f}')
    st.write(f'**Best suited for:** {fits[0][0]}. Also a good fit for {fits[1][0].lower()} and {fits[2][0].lower()}.')
    st.write(f'**Less suited for:** {fits[-1][0].lower()} relative to this phone’s other strengths.')
    left, right = st.columns(2)
    with left:
        st.subheader('Category ratings')
        for category in CATEGORIES:
            st.write(f'**{LABELS[category]}** — {scores[category]:.1f}/10')
            st.progress(scores[category] / 10)
        st.caption('Overall = unweighted mean of seven categories; value depends on entered price.')
    with right:
        st.subheader('Who is it for?')
        for label, fit in fits:
            st.write(f'{label}: **{fit:.1f}/10**')
        st.caption('Profile scores are weighted category matches, not probability of satisfaction.')
    st.subheader('Key specifications and features')
    for fact in phone.facts: st.write('• ' + fact)
    pos, neg = st.columns(2)
    with pos:
        st.subheader('Strengths')
        for item in phone.strengths: st.write('✅ ' + item)
    with neg:
        st.subheader('Trade-offs')
        for item in phone.weaknesses: st.write('⚠️ ' + item)
    if phone.note: st.warning(phone.note)
    st.success(f'**Purchase verdict:** {phone.name} is most compelling for {fits[0][0].lower()}. Check its weaker categories and actual local price before deciding.')

st.divider()
st.subheader('Compare two phones')
with st.form('compare_form'):
    c1,c2 = st.columns(2)
    with c1:
        name1 = st.selectbox('First phone', names, index=0)
        price1 = st.number_input('First phone price (₹)', min_value=1000, max_value=500000, value=60000, step=500)
    with c2:
        name2 = st.selectbox('Second phone', names, index=names.index('OnePlus 13s'))
        price2 = st.number_input('Second phone price (₹)', min_value=1000, max_value=500000, value=62000, step=500)
    compare = st.form_submit_button('Compare phones', use_container_width=True)
if compare:
    p1 = next(p for p in PHONES if p.name == name1)
    p2 = next(p for p in PHONES if p.name == name2)
    s1, o1, f1, *_ = scores_for(p1, p1.ram, p1.storage, price1)
    s2, o2, f2, *_ = scores_for(p2, p2.ram, p2.storage, price2)
    st.caption('Comparison uses each phone’s reference RAM/storage variant, and the prices entered above.')
    st.table([{'Category': LABELS[c], name1: f'{s1[c]:.1f}', name2: f'{s2[c]:.1f}'} for c in CATEGORIES] + [{'Category':'OVERALL',name1:f'{o1:.1f}',name2:f'{o2:.1f}'}])
    st.write(f'**Higher overall score:** {name1 if o1>o2 else name2 if o2>o1 else "Tie"}. Choose based on your priorities, not only the overall number.')

with st.expander('About the engine and limitations'):
    st.write('This is a curated offline database. To add phones, edit PHONES in engine.py. It deliberately does not guess ratings for unlisted phones. Prices, editorial scores and specifications should be reviewed regularly. Battery health and repair history are not evaluated for used devices.')
