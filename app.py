# streamlit_app.py
import streamlit as st
from crawler import get_weather_data
import sqlite3
import pandas as pd
import os
import altair as alt

AUTO_REFRESH_INTERVAL = 1800  # 每 30 分鐘刷新一次（秒）

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

# 自動刷新
st_autorefresh = st.experimental_data_editor([], key="autorefresh")
st_autorefresh

# 抓取資料
with st.spinner("Fetching weather data from CWA..."):
    weather_data, df = get_weather_data(api_key)

if isinstance(weather_data, str):
    st.error(weather_data)
    st.stop()

if not weather_data:
    st.warning("No data returned from CWA API.")
    st.stop()

# 選擇地區
locations = sorted(weather_data.keys())
selected_location = st.selectbox("Select a location", locations)

if selected_location:
    temps = weather_data[selected_location]
    min_temp = temps.get("MinT", "N/A")
    max_temp = temps.get("MaxT", "N/A")
    col1, col2 = st.columns(2)
    col1.metric("🌡️ Minimum Temperature (°C)", f"{min_temp} °C")
    col2.metric("🔥 Maximum Temperature (°C)", f"{max_temp} °C")

st.markdown("---")
st.subheader("📊 Latest 20 records")

# 從 SQLite 讀取最新 20 筆
conn = sqlite3.connect("weather.db")
df_sqlite = pd.read_sql_query(
    "SELECT * FROM weather ORDER BY obs_time DESC LIMIT 20", conn
)
conn.close()
st.dataframe(df_sqlite)

# 歷史折線圖
st.markdown("---")
st.subheader("📈 Historical Temperature Trend")

conn = sqlite3.connect("weather.db")
df_hist = pd.read_sql_query(
    "SELECT * FROM weather ORDER BY obs_time ASC", conn
)
conn.close()

if not df_hist.empty:
    selected_location_chart = st.selectbox(
        "Select location for trend chart",
        sorted(df_hist["location"].unique())
    )

    df_plot = df_hist[df_hist["location"] == selected_location_chart]
    df_plot["ObsTime"] = pd.to_datetime(df_plot["obs_time"])

    chart = alt.Chart(df_plot).transform_fold(
        ["min_temp", "max_temp"],
        as_=["Temperature_Type", "Temperature"]
    ).mark_line(point=True).encode(
        x="ObsTime:T",
        y="Temperature:Q",
        color="Temperature_Type:N",
        tooltip=["ObsTime:T", "Temperature:Q", "Temperature_Type:N"]
    ).properties(
        width=700,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No historical data available for trend chart.")

st.markdown("---")
st.info(f"Data source: Taiwan Central Weather Administration (CWA). Page refreshes every {AUTO_REFRESH_INTERVAL//60} minutes.")

st.experimental_rerun()
