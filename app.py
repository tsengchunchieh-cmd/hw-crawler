import streamlit as st
from crawler import get_weather_data

def main():
    """
    Main function to run the Streamlit web application.
    """
    st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🇹🇼")
    st.title("🇹🇼 Taiwan Weather Forecast")
    st.caption("A simple app to display temperature forecasts for various locations in Taiwan.")

    # API Key input
    st.sidebar.header("Configuration")
    api_key_help = "Get your free API key from the [CWA Open Data Platform](https://opendata.cwa.gov.tw/user/authkey)."
    api_key = st.sidebar.text_input(
        "Enter your CWA API Key",
        value='CWA-B4D7322F-5C4D-4493-96A6-A22223631758', # Example key
        help=api_key_help
    )

    if api_key:
        # Fetch data using the crawler function
        with st.spinner("Fetching weather data..."):
            weather_data = get_weather_data(api_key)

        if isinstance(weather_data, dict) and weather_data:
            st.sidebar.success("Data loaded successfully!")
            
            # Location selector
            locations = sorted(list(weather_data.keys()))
            selected_location = st.selectbox("Select a location", locations)

            if selected_location:
                st.header(f"Forecast for {selected_location}", divider="rainbow")
                temps = weather_data[selected_location]
                min_temp = temps.get('MinT', 'N/A')
                max_temp = temps.get('MaxT', 'N/A')

                col1, col2 = st.columns(2)
                col1.metric(label="🌡️ Minimum Temperature", value=min_temp)
                col2.metric(label="🔥 Maximum Temperature", value=max_temp)
        
        elif isinstance(weather_data, dict) and not weather_data:
            st.warning("The API key seems valid, but returned no data. The CWA data source might be temporarily unavailable.")
        
        else:
            st.error(f"Failed to fetch or parse weather data. Please check your API key and network connection. Error: {weather_data}")
    else:
        st.warning("Please enter a CWA API key in the sidebar to begin.")

    st.markdown("---")
    st.info("This application uses data from Taiwan's Central Weather Administration (CWA).")


if __name__ == "__main__":
    main()
