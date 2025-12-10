# streamlit_app.py
import streamlit as st
from crawler import get_weather_data
import sqlite3
import pandas as pd

def main():
    st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🇹🇼")
    st.title("🇹🇼 Taiwan Weather Forecast")
    st.caption("Historical and latest minimum/maximum temperatures for Taiwan.")

    # 抓取資料並存 SQLite
    with st.spinner("Fetching weather data from CWA..."):
        weather_data, df = get_weather_data()

    if isinstance(weather_data, str):
        st.error(weather_data)
        return

    if not weather_data:
        st.warning("No data returned from CWA API.")
        return

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

    st.markdown("---")
    st.info("Data source: Taiwan Central Weather Administration (CWA)")

if __name__ == "__main__":
    main()
