# app.py
import os
import uuid
import random
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from geopy.distance import geodesic

# ------------------------
# Page config
# ------------------------
st.set_page_config(
    page_title="SafeTravel - Crime Awareness & Safety Mapping",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------
# Mock data generators
# ------------------------
def generate_crime_data():
    areas = ['Gomti Nagar', 'Hazratganj', 'Aliganj', 'Indira Nagar', 'Aminabad', 'Jankipuram']
    crime_types = ['Robbery', 'Theft', 'Snatching', 'Assault', 'Burglary', 'Pickpocketing']
    crimes = []
    for i in range(50):
        area = random.choice(areas)
        crime = {
            'id': i + 1,
            'crime_type': random.choice(crime_types),
            'area': area,
            'severity': random.choice(['LOW', 'MEDIUM', 'HIGH']),
            'timestamp': datetime.now() - timedelta(days=random.randint(0, 30)),
            'reports': random.randint(1, 20),
            'lat': 26.85 + random.uniform(-0.05, 0.05),
            'lon': 80.94 + random.uniform(-0.05, 0.05),
            'source': 'mock'
        }
        crimes.append(crime)
    return pd.DataFrame(crimes)

def generate_safe_locations():
    safe_spots = [
        {'name': 'Police Station Gomti Nagar', 'type': 'police', 'lat': 26.8465, 'lon': 80.9462},
        {'name': 'Women Help Booth Hazratganj', 'type': 'pink_booth', 'lat': 26.8512, 'lon': 80.9415},
        {'name': 'Police Station Aliganj', 'type': 'police', 'lat': 26.8489, 'lon': 80.9387},
        {'name': 'Safe Zone Indira Nagar', 'type': 'safe_zone', 'lat': 26.8534, 'lon': 80.9491},
        {'name': 'Women Police Booth Aminabad', 'type': 'pink_booth', 'lat': 26.8471, 'lon': 80.9356},
        {'name': 'Police Outpost Jankipuram', 'type': 'police', 'lat': 26.8567, 'lon': 80.9423},
        {'name': '24/7 Help Center', 'type': 'safe_zone', 'lat': 26.8501, 'lon': 80.9448},
    ]
    return pd.DataFrame(safe_spots)

def generate_user_reports():
    reports = []
    areas = ['Gomti Nagar', 'Hazratganj', 'Aliganj', 'Indira Nagar', 'Aminabad']
    for i in range(15):
        report = {
            'id': str(uuid.uuid4()),
            'user': f'User_{random.randint(1000, 9999)}',
            'crime_type': random.choice(['Suspicious activity', 'Theft attempt', 'Harassment', 'Snatching']),
            'area': random.choice(areas),
            'description': f'Incident reported near {random.choice(["market", "park", "metro station", "shopping complex"])}',
            'timestamp': datetime.now() - timedelta(hours=random.randint(1, 72)),
            'verified': random.choice([True, False, False, False]),
            'lat': 26.85 + random.uniform(-0.03, 0.03),
            'lon': 80.94 + random.uniform(-0.03, 0.03)
        }
        reports.append(report)
    return pd.DataFrame(reports)

# ------------------------
# Load (or create) data and keep in session_state
# ------------------------
@st.cache_data
def create_initial_data():
    return {
        'crimes': generate_crime_data(),
        'safe_locations': generate_safe_locations(),
        'user_reports': generate_user_reports()
    }

if 'app_data' not in st.session_state:
    st.session_state.app_data = create_initial_data()

# Load persisted reports if exist
REPORTS_FILE = "reports.csv"
if os.path.exists(REPORTS_FILE):
    try:
        saved = pd.read_csv(REPORTS_FILE, parse_dates=['timestamp'])
        # merge with session reports (avoid duplicates by id)
        existing_ids = set(st.session_state.app_data['user_reports']['id'].astype(str).tolist())
        for _, row in saved.iterrows():
            if str(row['id']) not in existing_ids:
                st.session_state.app_data['user_reports'] = pd.concat(
                    [st.session_state.app_data['user_reports'], pd.DataFrame([row])],
                    ignore_index=True
                )
    except Exception:
        pass

# ------------------------
# Sidebar UI
# ------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/security-checked.png", width=80)
st.sidebar.title("SafeTravel 🛡️")
st.sidebar.markdown("---")

user_mode = st.sidebar.radio(
    "Select Your Mode:",
    ["👤 Traveler", "👩 Women", "🚔 Police Station"],
    help="Choose your viewing mode for personalized safety information"
)

st.sidebar.markdown("### 🔍 Filters")
time_filter = st.sidebar.selectbox(
    "Time Range:",
    ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
)

radius = st.sidebar.slider("Alert Radius (meters):", 200, 2000, 500)

crime_types = st.sidebar.multiselect(
    "Crime Types:",
    ['Robbery', 'Theft', 'Snatching', 'Assault', 'Burglary', 'Pickpocketing'],
    default=['Robbery', 'Theft', 'Snatching']
)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 My Location")

# Detect my location button (demo fixed coords)
if 'user_location' not in st.session_state:
    st.session_state.user_location = None

if st.sidebar.button("📍 Detect My Location"):
    # In a real app, you'd collect browser geolocation or mobile GPS. Here use demo coords.
    st.session_state.user_location = (26.8465, 80.9462)
    st.sidebar.success("Location detected (demo).")

# Allow manual override of location (optional)
st.sidebar.markdown("Or enter location manually:")
user_lat_input = st.sidebar.number_input("Latitude", value=st.session_state.user_location[0] if st.session_state.user_location else 26.8465, format="%.6f")
user_lon_input = st.sidebar.number_input("Longitude", value=st.session_state.user_location[1] if st.session_state.user_location else 80.9462, format="%.6f")
use_manual_loc = st.sidebar.checkbox("Use manual coordinates", value=False)
if use_manual_loc:
    st.session_state.user_location = (user_lat_input, user_lon_input)

# ------------------------
# Helper functions
# ------------------------
def filter_by_time(df, time_filter_val):
    now = datetime.now()
    if time_filter_val == "Last 24 Hours":
        since = now - timedelta(days=1)
    elif time_filter_val == "Last 7 Days":
        since = now - timedelta(days=7)
    elif time_filter_val == "Last 30 Days":
        since = now - timedelta(days=30)
    else:
        since = datetime.min
    return df[df['timestamp'] >= since]

def incidents_within_radius(df, user_loc, radius_m):
    nearby = []
    for _, row in df.iterrows():
        d_m = geodesic((user_loc[0], user_loc[1]), (row['lat'], row['lon'])).meters
        if d_m <= radius_m:
            nearby.append((row, d_m))
    # sort by distance
    nearby.sort(key=lambda x: x[1])
    return nearby

# ------------------------
# Main layout
# ------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📍 Live Safety Map")
    st.markdown("Real-time crime hotspots and safe zones in your area")

    # Build filtered crimes dataframe
    crimes_df = st.session_state.app_data['crimes'].copy()
    # apply time filter
    crimes_df = filter_by_time(crimes_df, time_filter)
    # apply crime types filter if any selected
    if crime_types:
        crimes_df = crimes_df[crimes_df['crime_type'].isin(crime_types)]

    # Folium map centered on Lucknow or user
    center = st.session_state.user_location if st.session_state.user_location else (26.85, 80.94)
    m = folium.Map(location=center, zoom_start=13)

    # Add user marker & safety circle if user location is known
    if st.session_state.user_location:
        folium.Marker(
            location=st.session_state.user_location,
            popup="📍 You are here",
            tooltip="Your location",
            icon=folium.Icon(color='blue', icon='user', prefix='fa')
        ).add_to(m)

        folium.Circle(
            location=st.session_state.user_location,
            radius=radius,
            popup=f"Safety radius ({radius} m)",
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.08,
            weight=2
        ).add_to(m)

    # Add crime markers (ONLY filtered crimes)
    for _, crime in crimes_df.iterrows():
        color = 'red' if crime['severity'] == 'HIGH' else 'orange' if crime['severity'] == 'MEDIUM' else 'yellow'
        folium.CircleMarker(
            location=[crime['lat'], crime['lon']],
            radius=7,
            popup=f"{crime['crime_type']} - {crime['area']}<br><small>{crime['timestamp'].strftime('%Y-%m-%d')}</small>",
            tooltip=f"Severity: {crime['severity']}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6
        ).add_to(m)

    # Add safe location markers (respect user_mode: show prominent in Women mode)
    for _, safe in st.session_state.app_data['safe_locations'].iterrows():
        if user_mode == "👩 Women":
            # show all safe locations in Women mode
            icon_color = 'pink' if safe['type'] == 'pink_booth' else 'blue' if safe['type'] == 'police' else 'green'
        else:
            # show police in general mode, keep others visible
            icon_color = 'blue' if safe['type'] == 'police' else 'green'
        icon_name = 'shield' if safe['type'] == 'police' else 'female' if safe['type'] == 'pink_booth' else 'home'
        folium.Marker(
            location=[safe['lat'], safe['lon']],
            popup=f"{safe['name']} - {safe['type'].replace('_',' ').title()}",
            tooltip="Safe Location",
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa')
        ).add_to(m)

    folium_static(m, width=800, height=520)

    # ------------------------
    # Alerts - proximity based
    # ------------------------
    st.subheader("🚨 Safety Alerts")

    if st.session_state.user_location:
        nearby_high = incidents_within_radius(crimes_df[crimes_df['severity'] == 'HIGH'], st.session_state.user_location, radius)
        if nearby_high:
            st.error(f"⚠️ HIGH ALERT: {len(nearby_high)} high-risk incident(s) within {radius} m of your location!")
            st.warning("Avoid isolated routes and stay in well-lit areas. Keep emergency contacts handy.")
            with st.expander("View Nearby High-Risk Incidents"):
                for row, dist in nearby_high[:10]:
                    st.write(f"• **{row['crime_type']}** in **{row['area']}** — {int(dist)} m away — {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        else:
            st.success("✅ No HIGH severity incidents within your selected radius.")
    else:
        st.info("📍 No detected location — use 'Detect My Location' or enter coordinates to enable proximity alerts.")

with col2:
    st.subheader("📊 Quick Stats")
    total_crimes = len(st.session_state.app_data['crimes'])
    high_risk = len(st.session_state.app_data['crimes'][st.session_state.app_data['crimes']['severity'] == 'HIGH'])
    community_reports = len(st.session_state.app_data['user_reports'])
    st.metric("Total Incidents (mock)", total_crimes)
    st.metric("High Risk Zones (mock)", high_risk)
    st.metric("Community Reports", community_reports)

    st.markdown("---")
    st.subheader("🏆 Safety Score")
    safety_score = max(0, 100 - (high_risk * 5))
    st.progress(safety_score / 100)
    st.markdown(f"**{safety_score}/100** - {'Excellent' if safety_score > 80 else 'Good' if safety_score > 60 else 'Moderate'}")

    st.markdown("---")
    st.subheader("🚨 Emergency Contacts")
    st.write("- **Police**: 100")
    st.write("- **Women Helpline**: 1091")
    st.write("- **Ambulance**: 102")
    st.write("- **Emergency**: 112")

# ------------------------
# Report Incident Section (persist to CSV)
# ------------------------
st.markdown("---")
st.header("📝 Report an Incident")

col3, col4 = st.columns(2)

with col3:
    with st.form("incident_report"):
        st.subheader("Community Reporting")
        incident_type = st.selectbox(
            "Incident Type:",
            ['Suspicious Activity', 'Theft', 'Harassment', 'Snatching', 'Other']
        )
        location_type = st.radio(
            "Location Detection:",
            ["Use Current Location", "Enter Coordinates", "Enter Area Name"]
        )
        description = st.text_area("Description of the incident:")
        urgency = st.slider("Urgency Level:", 1, 5, 3)
        photo = st.file_uploader("Add photo (optional):", type=['jpg', 'png'])
        submitted = st.form_submit_button("Submit Report")

        if submitted:
            # determine lat/lon
            if location_type == "Use Current Location" and st.session_state.user_location:
                lat, lon = st.session_state.user_location
                area_name = ""
            elif location_type == "Enter Coordinates":
                lat = st.number_input("Report Latitude", value=26.8465, format="%.6f", key="rep_lat")
                lon = st.number_input("Report Longitude", value=80.9462, format="%.6f", key="rep_lon")
                area_name = ""
            else:
                area_name = st.text_input("Area Name (e.g., Gomti Nagar)", key="rep_area")
                # For now we don't geocode area_name; place a placeholder near center
                lat, lon = 26.85 + random.uniform(-0.01, 0.01), 80.94 + random.uniform(-0.01, 0.01)

            new_report = {
                "id": str(uuid.uuid4()),
                "user": "anonymous",
                "crime_type": incident_type,
                "area": area_name,
                "description": description,
                "timestamp": datetime.now(),
                "verified": False,
                "lat": lat,
                "lon": lon
            }

            # append to session data
            st.session_state.app_data['user_reports'] = pd.concat(
                [st.session_state.app_data['user_reports'], pd.DataFrame([new_report])],
                ignore_index=True
            )

            # save to CSV for persistence
            df_save = pd.DataFrame([new_report])
            if os.path.exists(REPORTS_FILE):
                df_save.to_csv(REPORTS_FILE, mode='a', header=False, index=False)
            else:
                df_save.to_csv(REPORTS_FILE, index=False)
            st.success("✅ Report submitted successfully! Thank you for reporting.")
            st.balloons()

with col4:
    st.subheader("Recent Community Reports")
    recent_reports = st.session_state.app_data['user_reports'].sort_values('timestamp', ascending=False).head(6)
    for _, report in recent_reports.iterrows():
        verified_badge = " ✅" if report.get('verified', False) else ""
        ts = report['timestamp']
        # ensure ts is datetime-like for formatting
        try:
            ts_str = pd.to_datetime(ts).strftime('%Y-%m-%d %H:%M')
        except Exception:
            ts_str = str(ts)
        st.write(f"**{report['crime_type']}**{verified_badge}")
        st.write(f"*{report.get('area','Unknown')}* - {ts_str}")
        st.write(f"> {report.get('description','')}")
        st.markdown("---")

# ------------------------
# Women Safety block
# ------------------------
if user_mode == "👩 Women":
    st.markdown("---")
    st.header("👩 Women Safety Features")

    col5, col6 = st.columns(2)
    with col5:
        st.subheader("🛡️ Safe Route Planning (mock)")
        start = st.text_input("Start Location:", "Current Location")
        end = st.text_input("Destination:")
        if st.button("Find Safest Route"):
            st.info("""
**Recommended Safe Route (mock):**
- Prefer main roads with good lighting
- Prefer routes with police presence / safe booths
- Avoid isolated shortcuts
""")
    with col6:
        st.subheader("🔔 Safety Features")
        st.checkbox("Enable Live Location Sharing with trusted contacts")
        st.checkbox("Auto-alert when entering high-risk zones")
        st.checkbox("Quick emergency button on screen")
        st.checkbox("Night mode safety reminders")

# ------------------------
# Hotspot Analysis
# ------------------------
st.markdown("---")
st.header("🔥 Crime Hotspot Analysis")
area_stats = st.session_state.app_data['crimes'].groupby('area').agg({
    'severity': lambda x: (x == 'HIGH').sum(),
    'crime_type': 'count'
}).rename(columns={'crime_type': 'total_incidents', 'severity': 'high_risk_incidents'})

col7, col8, col9 = st.columns(3)
with col7:
    st.subheader("🔴 High Risk Areas")
    high_risk_areas = area_stats[area_stats['high_risk_incidents'] > 0].sort_values('high_risk_incidents', ascending=False)
    for area, stats in high_risk_areas.head(3).iterrows():
        st.write(f"**{area}**: {int(stats['high_risk_incidents'])} high-risk incidents")
with col8:
    st.subheader("🟡 Medium Risk Areas")
    st.write("Areas with moderate crime activity")
    for area in ['Hazratganj', 'Aliganj']:
        st.write(f"**{area}**: Exercise caution")
with col9:
    st.subheader("🟢 Safe Areas")
    st.write("Relatively safer zones")
    st.write("**Indira Nagar**: Low incident reports")
    st.write("**Aminabad**: Generally safe")

# ------------------------
# Footer and styles
# ------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🚀 Built with Streamlit | 🛡️ SafeTravel - Making Cities Safer</p>
    <p>⚠️ Demo data only. For real emergencies, contact local authorities immediately.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1f77b4; text-align: center; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)
