# streamlit_app.py
import streamlit as st
from crawler import get_weather_data

def main():
    st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🇹🇼")
    st.title("🇹🇼 Taiwan Weather Forecast")
    st.caption("Display minimum and maximum temperatures for various locations in Taiwan.")

    # Fetch data
    with st.spinner("Fetching weather data from CWA..."):
        weather_data = get_weather_data()

    if isinstance(weather_data, str):
        st.error(f"Failed to fetch weather data: {weather_data}")
        return

    if not weather_data:
        st.warning("No data returned from CWA API. Please try again later.")
        return

    # Location selector
    locations = sorted(weather_data.keys())
    selected_location = st.selectbox("Select a location", locations)

    if selected_location:
        temps = weather_data[selected_location]
        min_temp = temps.get("MinT", "N/A")
        max_temp = temps.get("MaxT", "N/A")

        st.subheader(f"Forecast for {selected_location}")
        col1, col2 = st.columns(2)
        col1.metric("🌡️ Minimum Temperature (°C)", f"{min_temp} °C")
        col2.metric("🔥 Maximum Temperature (°C)", f"{max_temp} °C")

    st.markdown("---")
    st.info("Data source: Taiwan Central Weather Administration (CWA)")

if __name__ == "__main__":
    main()
