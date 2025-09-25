import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import random
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import time

# Set page configuration
st.set_page_config(
    page_title="SafeTravel - Crime Awareness & Safety Mapping",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mock data generation functions
def generate_crime_data():
    """Generate mock crime data for demonstration"""
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
            'lon': 80.94 + random.uniform(-0.05, 0.05)
        }
        crimes.append(crime)
    
    return pd.DataFrame(crimes)

# Location feature - CORRECTED PLACEMENT
def add_location_feature():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 My Location")
    
    if st.sidebar.button("📍 Detect My Location"):
        user_lat, user_lon = 26.8465, 80.9462  # Demo coordinates
        return [user_lat, user_lon]
    return None

def generate_safe_locations():
    """Generate mock safe locations (police stations, pink booths)"""
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
    """Generate mock user reports"""
    reports = []
    areas = ['Gomti Nagar', 'Hazratganj', 'Aliganj', 'Indira Nagar', 'Aminabad']
    
    for i in range(15):
        report = {
            'id': i + 1,
            'user': f'User_{random.randint(1000, 9999)}',
            'crime_type': random.choice(['Suspicious activity', 'Theft attempt', 'Harassment', 'Snatching']),
            'area': random.choice(areas),
            'description': f'Incident reported near {random.choice(["market", "park", "metro station", "shopping complex"])}',
            'timestamp': datetime.now() - timedelta(hours=random.randint(1, 72)),
            'verified': random.choice([True, False, False, False]),  # 25% verified
            'lat': 26.85 + random.uniform(-0.03, 0.03),
            'lon': 80.94 + random.uniform(-0.03, 0.03)
        }
        reports.append(report)
    
    return pd.DataFrame(reports)

# Initialize data
@st.cache_data
def load_data():
    return {
        'crimes': generate_crime_data(),
        'safe_locations': generate_safe_locations(),
        'user_reports': generate_user_reports()
    }

data = load_data()

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/000000/security-checked.png", width=80)
st.sidebar.title("SafeTravel 🛡️")
st.sidebar.markdown("---")

# User mode selection - CORRECTED VALUES
user_mode = st.sidebar.radio(
    "Select Your Mode:",
    ["👤 Traveler", "👩 Women", "🚔 Police Station"],  # Fixed values
    help="Choose your viewing mode for personalized safety information"
)

# Filters
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

# Get user location FIRST - CORRECTED ORDER
user_location = add_location_feature()

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📍 Live Safety Map")
    st.markdown("Real-time crime hotspots and safe zones in your area")
    
    # Map section
    st.subheader("Interactive Safety Map")
    
    # Create a folium map
    m = folium.Map(location=[26.85, 80.94], zoom_start=12)
    
    # Add user location FIRST if detected - CORRECTED ORDER
    if user_location:
        # Add blue dot for user location
        folium.Marker(
            user_location,
            popup="📍 You are here!",
            tooltip="Your current location",
            icon=folium.Icon(color='blue', icon='user', prefix='fa')
        ).add_to(m)
        
        # Add safety radius circle
        folium.Circle(
            user_location,
            radius=radius,  # Use the selected radius
            popup=f"Your safety zone ({radius}m radius)",
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.1,
            weight=2
        ).add_to(m)
    
    # Add crime hotspots
    for _, crime in data['crimes'].iterrows():
        color = 'red' if crime['severity'] == 'HIGH' else 'orange' if crime['severity'] == 'MEDIUM' else 'yellow'
        folium.CircleMarker(
            location=[crime['lat'], crime['lon']],
            radius=8,
            popup=f"{crime['crime_type']} - {crime['area']}",
            tooltip=f"Severity: {crime['severity']}",
            color=color,
            fillColor=color,
            fillOpacity=0.6
        ).add_to(m)
    
    # Add safe locations
    for _, safe in data['safe_locations'].iterrows():
        icon_color = 'blue' if safe['type'] == 'police' else 'pink' if safe['type'] == 'pink_booth' else 'green'
        icon = 'shield-alt' if safe['type'] == 'police' else 'female' if safe['type'] == 'pink_booth' else 'home'
        
        folium.Marker(
            location=[safe['lat'], safe['lon']],
            popup=f"{safe['name']} - {safe['type'].replace('_', ' ').title()}",
            tooltip="Safe Location",
            icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
        ).add_to(m)
    
    # Display the map
    folium_static(m, width=800, height=500)
    
    # Alert system
    st.subheader("🚨 Safety Alerts")
    
    # Use detected location or default
    if user_location:
        user_lat, user_lon = user_location
        st.success("📍 Using your detected location for safety analysis")
    else:
        user_lat, user_lon = 26.8465, 80.9462  # Default location (Gomti Nagar)
        st.info("📍 Using default location. Click 'Detect My Location' for accurate analysis.")
    
    # Check for nearby high-risk areas
    high_risk_crimes = data['crimes'][
        (data['crimes']['severity'] == 'HIGH') & 
        (data['crimes']['crime_type'].isin(crime_types))
    ]
    
    alert_count = len(high_risk_crimes)
    
    if alert_count > 0:
        st.error(f"⚠️ HIGH ALERT: You are in an area with {alert_count} high-risk crime reports nearby!")
        st.warning("Avoid isolated routes and stay in well-lit areas. Keep emergency contacts handy.")
        
        # Show nearby high-risk crimes
        with st.expander("View Nearby High-Risk Incidents"):
            for _, crime in high_risk_crimes.head(3).iterrows():
                st.write(f"• **{crime['crime_type']}** in {crime['area']} ({(crime['reports'])} reports)")
    else:
        st.success("✅ Your current location appears to be relatively safe. Stay aware of your surroundings.")

with col2:
    st.subheader("📊 Quick Stats")
    
    # Statistics cards
    total_crimes = len(data['crimes'])
    high_risk = len(data['crimes'][data['crimes']['severity'] == 'HIGH'])
    community_reports = len(data['user_reports'])
    
    st.metric("Total Incidents", total_crimes)
    st.metric("High Risk Zones", high_risk)
    st.metric("Community Reports", community_reports)
    
    st.markdown("---")
    st.subheader("🏆 Safety Score")
    
    # Calculate safety score (mock)
    safety_score = max(0, 100 - (high_risk * 5))
    st.progress(safety_score / 100)
    st.markdown(f"**{safety_score}/100** - {'Excellent' if safety_score > 80 else 'Good' if safety_score > 60 else 'Moderate'}")
    
    st.markdown("---")
    st.subheader("🚨 Emergency Contacts")
    st.markdown("""
    - **Police**: 100
    - **Women Helpline**: 1091
    - **Ambulance**: 102
    - **Emergency**: 112
    """)

# Report Incident Section
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
            ["Use Current Location", "Select on Map", "Enter Manually"]
        )
        
        description = st.text_area("Description of the incident:")
        
        urgency = st.slider("Urgency Level:", 1, 5, 3)
        
        # Photo upload (mock)
        photo = st.file_uploader("Add photo (optional):", type=['jpg', 'png'])
        
        submitted = st.form_submit_button("Submit Report")
        
        if submitted:
            st.success("✅ Report submitted successfully! Our team will review it.")
            st.balloons()

with col4:
    st.subheader("Recent Community Reports")
    
    # Show recent user reports
    recent_reports = data['user_reports'].head(5)
    
    for _, report in recent_reports.iterrows():
        verified_badge = " ✅" if report['verified'] else ""
        st.write(f"""
        **{report['crime_type']}**{verified_badge}
        *{report['area']}* - {report['timestamp'].strftime('%Y-%m-%d %H:%M')}
        > {report['description']}
        """)
        st.markdown("---")

# Women Safety Features - CORRECTED CONDITION
if user_mode == "👩 Women":  # Fixed condition
    st.markdown("---")
    st.header("👩 Women Safety Features")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("🛡️ Safe Route Planning")
        start = st.text_input("Start Location:", "Current Location")
        end = st.text_input("Destination:")
        
        if st.button("Find Safest Route"):
            st.info("""
            **Recommended Safe Route:**
            - Main roads with good lighting
            - Areas with police presence
            - Avoid isolated shortcuts
            - Estimated safe travel time: 15 mins
            """)
    
    with col6:
        st.subheader("🔔 Safety Features")
        st.checkbox("Enable Live Location Sharing with trusted contacts")
        st.checkbox("Auto-alert when entering high-risk zones")
        st.checkbox("Quick emergency button on screen")
        st.checkbox("Night mode safety reminders")

# Hotspot Analysis
st.markdown("---")
st.header("🔥 Crime Hotspot Analysis")

# Area-wise crime distribution
area_stats = data['crimes'].groupby('area').agg({
    'severity': lambda x: (x == 'HIGH').sum(),
    'crime_type': 'count'
}).rename(columns={'crime_type': 'total_incidents', 'severity': 'high_risk_incidents'})

# Display hotspot analysis
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

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🚀 Built with Streamlit | 🛡️ SafeTravel - Making Cities Safer</p>
    <p>⚠️ This is a demonstration system. For real emergencies, contact local authorities immediately.</p>
</div>
""", unsafe_allow_html=True)

# CSS - CORRECTED SYNTAX
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ffcccc;
        padding: 1rem;
        border-left: 5px solid #ff0000;
        margin: 1rem 0;
    }
    .alert-medium {
        background-color: #fff0cc;
        padding: 1rem;
        border-left: 5px solid #ffaa00;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)