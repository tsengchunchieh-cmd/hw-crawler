# streamlit_app.py
import streamlit as st
from crawler import get_weather_data
import sqlite3
import pandas as pd
import os
import altair as alt
import time

st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🇹🇼")
st.title("🇹🇼 Taiwan Weather Forecast")
st.caption("Historical and latest minimum/maximum temperatures for Taiwan.")

# Sidebar 輸入 API Key
api_key_sidebar = st.sidebar.text_input(
    "Enter your CWA API Key",
    value="",
    help="You can also set environment variable CWA_API_KEY"
)
api_key_env = os.getenv("CWA_API_KEY", "")
api_key = api_key_sidebar.strip() or api_key_env.strip()

if not api_key:
    st.warning("Please provide your CWA API Key in the sidebar or via environment variable.")
    st.stop()

# 選擇單一地區即時顯示
locations = []
weather_data = {}
df_sqlite = pd.DataFrame()

def fetch_data():
    global weather_data, df_sqlite, locations
    weather_data, df = get_weather_data(api_key)
    if isinstance(weather_data, dict):
        locations = sorted(weather_data.keys())
    else:
        st.error(weather_data)
    conn = sqlite3.connect("weather.db")
    df_sqlite = pd.read_sql_query(
        "SELECT * FROM weather ORDER BY obs_time DESC LIMIT 50", conn
    )
    conn.close()

# 初次抓資料
with st.spinner("Fetching initial data from CWA..."):
    fetch_data()

# 自動刷新間隔（秒）
refresh_interval = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 60, 15)

# 顯示最新單一地區資料
selected_location = st.selectbox("Select a location for current temperature", locations)
if selected_location:
    temps = weather_data.get(selected_location, {})
    min_temp = temps.get("MinT", "N/A")
    max_temp = temps.get("MaxT", "N/A")
    col1, col2 = st.columns(2)
    col1.metric("🌡️ Minimum Temperature (°C)", f"{min_temp} °C")
    col2.metric("🔥 Maximum Temperature (°C)", f"{max_temp} °C")

st.markdown("---")
st.subheader("📊 Latest records")
data_container = st.empty()
data_container.dataframe(df_sqlite)

st.markdown("---")
st.subheader("📈 Historical Temperature Trend (Multiple Locations)")
chart_container = st.empty()
selected_locations_chart = st.multiselect(
    "Select locations for trend chart",
    locations,
    default=[locations[0]] if locations else []
)

# 自動刷新 loop
while True:
    fetch_data()

    # 更新最新資料表
    data_container.dataframe(df_sqlite)

    # 更新折線圖
    if not df_sqlite.empty and selected_locations_chart:
        df_plot = df_sqlite[df_sqlite["location"].isin(selected_locations_chart)]
        df_plot["ObsTime"] = pd.to_datetime(df_plot["obs_time"])
        df_melt = df_plot.melt(
            id_vars=["location", "ObsTime"],
            value_vars=["min_temp", "max_temp"],
            var_name="Temperature_Type",
            value_name="Temperature"
        )
        chart = alt.Chart(df_melt).mark_line(point=True).encode(
            x="ObsTime:T",
            y="Temperature:Q",
            color=alt.Color("location:N", title="Location"),
            strokeDash=alt.StrokeDash("Temperature_Type:N", title="Temperature Type"),
            tooltip=["ObsTime:T", "Temperature:Q", "location:N", "Temperature_Type:N"]
        ).properties(
            width=700,
            height=400
        )
        chart_container.altair_chart(chart, use_container_width=True)

    time.sleep(refresh_interval)
