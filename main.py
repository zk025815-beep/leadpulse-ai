import os
import json
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# --------------------------------------------------
# Page Configuration & Custom Modern CSS (Dark/Light Adaptive)
# --------------------------------------------------
st.set_page_config(
    page_title="LeadPulse AI | Smart Lead Qualifier",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Hero Banner */
    .hero-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #cbd5e1;
        margin: 0;
    }

    /* KPI Metric Cards */
    .kpi-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        text-align: center;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0.2rem 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Lead Cards */
    .lead-card {
        background: rgba(30, 41, 59, 0.65);
        border-radius: 14px;
        padding: 1.3rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .lead-card-hot {
        border-left: 6px solid #ef4444;
    }
    .lead-card-cold {
        border-left: 6px solid #3b82f6;
    }
    .badge-hot {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 4px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-cold {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 4px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
    }
    .lead-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .lead-meta {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin: 0.45rem 0;
    }
    .lead-reason {
        background: rgba(15, 23, 42, 0.65);
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        font-size: 0.9rem;
        color: #e2e8f0;
        margin-top: 0.65rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Supported Industries
# --------------------------------------------------
INDUSTRY_CATEGORIES = {
    "🍽️ Restaurant": "catering.restaurant",
    "☕ Cafe & Coffee Shop": "catering.cafe",
    "🏨 Hotel & Hospitality": "accommodation.hotel",
    "🛒 Supermarket & Grocery": "commercial.supermarket",
    "🥐 Bakery & Sweets": "catering.bakery"
}

# --------------------------------------------------
# Sidebar Controls
# --------------------------------------------------
# --------------------------------------------------
# Sidebar Controls
# --------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ LeadPulse AI")
    st.caption("High-Speed B2B Lead Generation & Qualification")
    st.divider()

    # Safely load keys from local .env OR Streamlit Cloud Secrets
    env_geo_key = os.getenv("GEOAPIFY_API_KEY", "")
    env_gem_key = os.getenv("GEMINI_API_KEY", "")

    if not env_geo_key or not env_gem_key:
        try:
            env_geo_key = st.secrets.get("GEOAPIFY_API_KEY", env_geo_key)
            env_gem_key = st.secrets.get("GEMINI_API_KEY", env_gem_key)
        except Exception:
            pass

    if env_geo_key and env_gem_key:
        geoapify_key = env_geo_key
        gemini_key = env_gem_key
        st.success("🔒 System API Keys Active")
    else:
        st.subheader("🔑 API Credentials")
        geoapify_key = st.text_input("Geoapify API Key", type="password")
        gemini_key = st.text_input("Gemini API Key", type="password")

    st.divider()
    st.subheader("🎯 Search Parameters")
    radius_km = st.slider("Search Radius (km)", min_value=1, max_value=25, value=10)
    lead_limit = st.slider("Max Leads to Fetch", min_value=5, max_value=30, value=10, step=5)
    selected_model = st.selectbox(
        "Gemini Model",
        ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"],
        index=0
    )

    st.divider()
    st.info("💡 **Speed Boost Enabled:** All leads are analyzed simultaneously in a single batch Gemini API call (~2 seconds).")

# --------------------------------------------------
# Backend Functions
# --------------------------------------------------
@st.cache_data(show_spinner=False, ttl=600)
def get_coordinates(location, api_key):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": f"{location}, Pakistan",
        "apiKey": api_key,
        "limit": 1
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        return None, None

    data = response.json()
    features = data.get("features", [])
    if not features:
        return None, None

    coords = features[0]["geometry"]["coordinates"]
    return coords[0], coords[1]  # lon, lat


def extract_leads(data):
    leads = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {}).get("coordinates", [None, None])
        categories = props.get("categories", [])

        leads.append({
            "name": props.get("name", "Unknown Business"),
            "website": props.get("website", "Not available"),
            "phone": props.get("contact", {}).get("phone", "Not available"),
            "location": props.get("formatted", "Not available"),
            "description": props.get("description", "Not available"),
            "categories": ", ".join(categories),
            "lon": geom[0],
            "lat": geom[1]
        })
    return leads


@st.cache_data(show_spinner=False, ttl=600)
def get_leads(category, location, radius_meters, limit, api_key):
    lon, lat = get_coordinates(location, api_key)
    if lon is None:
        return [], None, None

    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},{radius_meters}",
        "limit": limit,
        "apiKey": api_key
    }
    response = requests.get(url, params=params, timeout=15)
    if response.status_code != 200:
        return [], lon, lat

    return extract_leads(response.json()), lon, lat


def classify_all_leads_fast(client, leads, primary_model):
    """Classifies all leads in ONE single API request with automatic model fallback."""
    leads_payload = []
    for idx, lead in enumerate(leads):
        leads_payload.append({
            "id": idx,
            "name": lead["name"],
            "website": lead["website"],
            "phone": lead["phone"],
            "location": lead["location"],
            "categories": lead["categories"]
        })

    prompt = f"""
You are an expert B2B sales lead qualifier.
Analyze the following list of businesses and classify each one as either "HOT" or "COLD".

- "HOT": Known commercial brand, clear business name, established venue/hotel/restaurant/supermarket, or has website/phone/strong location presence.
- "COLD": Unnamed ("Unknown Business"), vague/incomplete data, or very low commercial potential.

Return ONLY a valid JSON array where each object has:
- "id": (integer matching the input id)
- "classification": "HOT" or "COLD"
- "score": integer from 1 to 10 indicating lead quality
- "reason": One concise sentence explaining why.

Input Leads:
{json.dumps(leads_payload, ensure_ascii=False)}
"""

    # Try selected model first, then fallback models if needed
    models_to_try = [primary_model] + [
        m for m in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
        if m != primary_model
    ]

    last_error = None
    for model_id in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            continue

    raise last_error

# --------------------------------------------------
# Main Hero Header
# --------------------------------------------------
st.markdown("""
<div class="hero-box">
    <div class="hero-title">⚡ LeadPulse AI — Smart B2B Lead Discovery</div>
    <div class="hero-sub">Discover local businesses via Geoapify & instantly qualify HOT prospects in seconds with Google Gemini AI.</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Search Bar Section
# --------------------------------------------------
with st.container():
    with st.form("search_form"):
        c1, c2, c3 = st.columns([2, 2.5, 1.2])
        with c1:
            industry_label = st.selectbox("🏢 Select Target Industry", list(INDUSTRY_CATEGORIES.keys()))
        with c2:
            location_query = st.text_input("📍 Target Area & City", value="Chungi No 6, Multan", placeholder="e.g., Gulgasht Colony, Multan")
        with c3:
            st.write("")
            st.write("")
            run_search = st.form_submit_button("🚀 Analyze Leads", use_container_width=True)

# --------------------------------------------------
# Execution Logic
# --------------------------------------------------
if run_search:
    if not geoapify_key or not gemini_key:
        st.error("🔑 Please enter both your **Geoapify** and **Gemini** API keys in the sidebar or `.env` file.")
    elif not location_query.strip():
        st.warning("⚠️ Please enter a valid location.")
    else:
        category_code = INDUSTRY_CATEGORIES[industry_label]

        with st.status("🚀 Running AI Lead Discovery Pipeline...", expanded=True) as status:
            st.write(f"📡 Geocoding **{location_query}** and fetching up to **{lead_limit}** businesses...")
            leads, center_lon, center_lat = get_leads(
                category_code, location_query, radius_km * 1000, lead_limit, geoapify_key
            )

            if center_lon is None:
                status.update(label="❌ Location could not be found!", state="error", expanded=True)
                st.stop()
            elif not leads:
                status.update(label="⚠️ No leads found in this radius.", state="warning", expanded=True)
                st.stop()

            st.write(f"✅ Found **{len(leads)}** businesses! Running single-batch Gemini AI qualification...")

            try:
                client = genai.Client(api_key=gemini_key)
                ai_results = classify_all_leads_fast(client, leads, selected_model)
                ai_map = {item["id"]: item for item in ai_results}
            except Exception as e:
                status.update(label="❌ Gemini API Error", state="error", expanded=True)
                st.error(f"Error details: {e}")
                st.stop()

            final_rows = []
            for idx, lead in enumerate(leads):
                ai_info = ai_map.get(idx, {"classification": "COLD", "score": 5, "reason": "No analysis returned."})
                cls_tag = str(ai_info.get("classification", "COLD")).upper()

                final_rows.append({
                    "Business": lead["name"],
                    "Status": "HOT" if "HOT" in cls_tag else "COLD",
                    "Score": ai_info.get("score", 5),
                    "Reason": ai_info.get("reason", ""),
                    "Location": lead["location"],
                    "Phone": lead["phone"],
                    "Website": lead["website"],
                    "Categories": lead["categories"],
                    "lat": lead["lat"],
                    "lon": lead["lon"]
                })

            st.session_state["leads_df"] = pd.DataFrame(final_rows)
            st.session_state["search_meta"] = f"{industry_label} near {location_query}"
            status.update(label=f"🎉 Successfully qualified {len(final_rows)} leads in seconds!", state="complete", expanded=False)

# --------------------------------------------------
# Interactive Results Dashboard
# --------------------------------------------------
if "leads_df" in st.session_state:
    df = st.session_state["leads_df"]

    total_count = len(df)
    hot_count = len(df[df["Status"] == "HOT"])
    cold_count = len(df[df["Status"] == "COLD"])
    avg_score = round(df["Score"].mean(), 1) if total_count > 0 else 0

    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Leads</div><div class="kpi-value" style="color:#f8fafc;">{total_count}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🔥 Hot Prospects</div><div class="kpi-value" style="color:#f87171;">{hot_count}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">❄️ Cold Prospects</div><div class="kpi-value" style="color:#60a5fa;">{cold_count}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">⭐ Avg Quality Score</div><div class="kpi-value" style="color:#34d399;">{avg_score}/10</div></div>', unsafe_allow_html=True)

    st.write("")

    # Filter & Action Bar
    f_col1, f_col2, f_col3 = st.columns([2, 2, 1.2])
    with f_col1:
        filter_status = st.segmented_control(
            "Filter by Classification",
            options=["All Leads", "🔥 HOT Only", "❄️ COLD Only"],
            default="All Leads"
        )
    with f_col2:
        search_text = st.text_input("🔍 Filter by Business Name or Address", placeholder="Type to filter results...")
    with f_col3:
        st.write("")
        csv_bytes = df.drop(columns=["lat", "lon"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Export to CSV",
            data=csv_bytes,
            file_name="lead_generation_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Apply Filters
    filtered_df = df.copy()
    if filter_status == "🔥 HOT Only":
        filtered_df = filtered_df[filtered_df["Status"] == "HOT"]
    elif filter_status == "❄️ COLD Only":
        filtered_df = filtered_df[filtered_df["Status"] == "COLD"]

    if search_text.strip():
        filtered_df = filtered_df[
            filtered_df["Business"].str.contains(search_text, case=False, na=False) |
            filtered_df["Location"].str.contains(search_text, case=False, na=False)
        ]

    # Dashboard Views: Visual Cards, Data Table, Map View
    tab_cards, tab_table, tab_map = st.tabs([
        "🗂️ Visual Lead Cards",
        "📊 Interactive Data Table",
        "🗺️ Geographic Map View"
    ])

    with tab_cards:
        if filtered_df.empty:
            st.info("No leads match the selected filter.")
        else:
            card_cols = st.columns(2)
            for idx, (_, row) in enumerate(filtered_df.iterrows()):
                is_hot = row["Status"] == "HOT"
                card_class = "lead-card-hot" if is_hot else "lead-card-cold"
                badge_html = f'<span class="badge-hot">🔥 HOT • {row["Score"]}/10</span>' if is_hot else f'<span class="badge-cold">❄️ COLD • {row["Score"]}/10</span>'

                with card_cols[idx % 2]:
                    st.markdown(f"""
                    <div class="lead-card {card_class}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div class="lead-title">{row['Business']}</div>
                            {badge_html}
                        </div>
                        <div class="lead-meta">📍 {row['Location']}</div>
                        <div class="lead-meta">📞 <b>Phone:</b> {row['Phone']} &nbsp;|&nbsp; 🌐 <b>Web:</b> {row['Website']}</div>
                        <div class="lead-reason">💡 <b>AI Insight:</b> {row['Reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    with tab_table:
        display_df = filtered_df[["Business", "Status", "Score", "Reason", "Location", "Phone", "Website"]].copy()
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Lead Score (1-10)",
                    format="%d / 10",
                    min_value=1,
                    max_value=10
                )
            }
        )

    with tab_map:
        map_df = filtered_df.dropna(subset=["lat", "lon"]).copy()
        if not map_df.empty:
            st.caption("📍 Pin locations of discovered leads in your target area:")
            st.map(map_df, latitude="lat", longitude="lon", size=40)
        else:
            st.info("No coordinate data available to display on map.")