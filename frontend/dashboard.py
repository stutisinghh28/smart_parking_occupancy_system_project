"""
Streamlit Dashboard for Smart Parking Occupancy Predictor.
Visualizes 6 parking slots, real-time ultrasonic sensor measurements,
LED indicator states, historical trends, and Echo State Network (ESN) predictions.
"""

import time
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# Streamlit Page Configuration
st.set_page_config(
    page_title="Smart Parking Occupancy Predictor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling and parking bay cards
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .slot-card {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease;
    }
    .slot-card:hover {
        transform: translateY(-2px);
    }
    .slot-free {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 2px solid #10B981;
    }
    .slot-occupied {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #EF4444;
    }
    .slot-header {
        font-size: 1.25rem;
        font-weight: 700;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .led-pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .led-green {
        background-color: #10B981;
        color: white;
    }
    .led-red {
        background-color: #EF4444;
        color: white;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        margin-top: 0.5rem;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #475569;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("⚙️ System Control")
api_base_url = st.sidebar.text_input("FastAPI Backend URL", value="http://127.0.0.1:8000")

auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=True)
refresh_interval = st.sidebar.slider("Refresh rate (seconds)", min_value=1, max_value=10, value=3)

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Sensor Simulation")

if st.sidebar.button("Trigger Random Car Movement"):
    try:
        sim_res = requests.post(f"{api_base_url}/api/telemetry", json={
            "readings": [
                {
                    "slot_id": i,
                    "distance_cm": 35.0 if i % 2 == 0 else 210.0,
                    "is_occupied": (i % 2 == 0),
                    "echo_time_us": (35.0 if i % 2 == 0 else 210.0) * 58.2
                }
                for i in range(1, 7)
            ]
        }, timeout=2.0)
        if sim_res.status_code == 200:
            st.sidebar.success("Test batch ingested!")
    except Exception as e:
        st.sidebar.error(f"Failed to post: {e}")

if st.sidebar.button("Seed 30 Historical Data Points"):
    try:
        import random
        for _ in range(30):
            readings = []
            for s in range(1, 7):
                occ = random.choice([True, False])
                dist = round(random.uniform(25.0, 50.0) if occ else random.uniform(190.0, 220.0), 1)
                readings.append({
                    "slot_id": s,
                    "distance_cm": dist,
                    "is_occupied": occ,
                    "echo_time_us": round(dist * 58.2, 1)
                })
            requests.post(f"{api_base_url}/api/telemetry", json={"readings": readings}, timeout=2.0)
        st.sidebar.success("Seeded 30 snapshots!")
    except Exception as e:
        st.sidebar.error(f"Seeding error: {e}")

# Helper Functions
def fetch_status():
    try:
        r = requests.get(f"{api_base_url}/api/status", timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

def fetch_forecast():
    try:
        r = requests.get(f"{api_base_url}/api/forecast", timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

def fetch_history():
    try:
        r = requests.get(f"{api_base_url}/api/history?limit=40", timeout=2.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return []
    return []

# App Header
st.markdown('<div class="main-title">🚗 Smart Parking Occupancy Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">STM32 + 6x HC-SR04 + ESP8266 IoT Hub | Echo State Network (ESN) Forecasting Engine</div>', unsafe_allow_html=True)

# Fetch latest data
status_data = fetch_status()
forecast_data = fetch_forecast()
history_data = fetch_history()

if status_data is None:
    st.warning("⚠️ Cannot connect to FastAPI backend. Make sure the backend server is running at " + api_base_url)
    st.info("Run `python -m uvicorn backend.main:app --reload` to start the backend.")
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    st.stop()

# Top Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Slots", f"{status_data['total_slots']}")

with col2:
    st.metric("Currently Free", f"{status_data['free_count']} / 6", delta=f"{status_data['occupied_count']} Occupied", delta_color="inverse")

with col3:
    st.metric("Occupancy Rate", f"{(status_data['occupied_count'] / 6.0) * 100:.0f}%")

with col4:
    if forecast_data:
        st.metric(
            "ESN Forecast (+15m)",
            f"{forecast_data['horizon_15min_rounded']} free",
            delta=f"{forecast_data['predicted_free_15min']:.1f} continuous",
            delta_color="normal"
        )
    else:
        st.metric("ESN Forecast (+15m)", "N/A")

with col5:
    if forecast_data:
        st.metric(
            "ESN Forecast (+30m)",
            f"{forecast_data['horizon_30min_rounded']} free",
            delta=f"{forecast_data['predicted_free_30min']:.1f} continuous",
            delta_color="normal"
        )
    else:
        st.metric("ESN Forecast (+30m)", "N/A")

st.markdown("---")

# Parking Lot Real-Time Bay Visualization (6 Slots Grid)
st.subheader("🅿️ Parking Bay Grid & Physical LED Indicators")

slots = status_data["slots"]
row1_cols = st.columns(3)
row2_cols = st.columns(3)

for idx, slot in enumerate(slots):
    col = row1_cols[idx] if idx < 3 else row2_cols[idx - 3]
    is_occ = slot["is_occupied"]
    card_class = "slot-occupied" if is_occ else "slot-free"
    led_class = "led-red" if is_occ else "led-green"
    led_text = "RED LED ON (OCCUPIED)" if is_occ else "GREEN LED ON (VACANT)"
    status_icon = "🚘" if is_occ else "🟢"
    status_badge = "OCCUPIED" if is_occ else "VACANT"

    with col:
        st.markdown(f"""
        <div class="slot-card {card_class}">
            <div class="slot-header">
                <span>Slot {slot['slot_id']} {status_icon}</span>
                <span class="led-pill {led_class}">{status_badge}</span>
            </div>
            <div class="metric-value">{slot['distance_cm']:.1f} cm</div>
            <div class="metric-sub"><b>Hardware LED:</b> {led_text}</div>
            <div class="metric-sub"><b>Ultrasonic Echo:</b> ~{slot['distance_cm'] * 58.2:.0f} µs</div>
            <div class="metric-sub"><b>Threshold:</b> &lt; 80 cm</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Forecasting & Historical Trends Charts
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 Occupancy History & ESN Projection")
    if history_data:
        df_hist = pd.DataFrame(history_data)
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        df_hist = df_hist.sort_values("timestamp")
        
        # Display line chart
        chart_df = df_hist.set_index("timestamp")[["free_count", "occupied_count"]]
        st.line_chart(chart_df, color=["#10B981", "#EF4444"])
    else:
        st.info("No historical data available yet. Start the simulator or seed data to view graphs.")

with chart_col2:
    st.subheader("🧠 Echo State Network Insights")
    if forecast_data:
        st.write(f"**ML Engine:** {forecast_data['model_algorithm']}")
        st.write(f"**Current Free Spaces:** `{forecast_data['current_free']}`")
        st.write(f"**Predicted @ +15 min:** `{forecast_data['predicted_free_15min']} slots` (Round: {forecast_data['horizon_15min_rounded']})")
        st.write(f"**Predicted @ +30 min:** `{forecast_data['predicted_free_30min']} slots` (Round: {forecast_data['horizon_30min_rounded']})")
        
        st.caption("The ESN model uses dynamic recurrent reservoir state transitions to forecast commuter arrival/departure momentum without needing heavy deep-learning runtimes.")
    else:
        st.info("Forecast data not loaded.")

# Auto-refresh loop
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
