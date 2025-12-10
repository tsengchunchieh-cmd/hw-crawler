import requests
import xml.etree.ElementTree as ET

def get_weather_data(api_key):
    """
    Fetches weather data from the CWA open data API and parses the XML response.

    Args:
        api_key (str): The authorization key for the CWA API.

    Returns:
        dict or str: A dictionary containing temperature data for each location,
                     or an error message string if fetching or parsing fails.
    """
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={api_key}&format=XML"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

    try:
        root = ET.fromstring(response.content)
        locations = {}
        # The XML has a namespace, which we need to use to find elements
        ns = {'cwa': 'urn:cwa:gov:tw:cwacommon:0.1'}

        for location in root.findall('.//cwa:location', ns):
            location_name = location.find('cwa:locationName', ns).text
            weather_elements = {}
            for element in location.findall('cwa:weatherElement', ns):
                element_name = element.find('cwa:elementName', ns).text
                # We are interested in MinT (Minimum Temperature) and MaxT (Maximum Temperature)
                if element_name in ['MinT', 'MaxT']:
                    # Extract the temperature value and unit
                    time_element = element.find('cwa:time', ns)
                    temp = time_element.find('.//cwa:parameterName', ns).text
                    unit = time_element.find('.//cwa:parameterUnit', ns).text
                    weather_elements[element_name] = f"{temp} {unit}"
            locations[location_name] = weather_elements
        return locations
    except ET.ParseError as e:
        return f"Error parsing XML: {e}"

if __name__ == '__main__':
    # This is an example API key from the CWA documentation.
    # It is recommended to get your own key from: https://opendata.cwa.gov.tw/
    # This key may be rate-limited or disabled in the future.
    example_api_key = 'CWA-B4D7322F-5C4D-4493-96A6-A22223631758'
    
    weather_data = get_weather_data(example_api_key)
    
    if isinstance(weather_data, dict):
        print("Successfully fetched and parsed weather data.")
        for location, temps in list(weather_data.items())[:5]: # Print first 5 for brevity
            print(f"\nLocation: {location}")
            min_temp = temps.get('MinT', 'N/A')
            max_temp = temps.get('MaxT', 'N/A')
            print(f"  Minimum Temperature: {min_temp}")
            print(f"  Maximum Temperature: {max_temp}")
    else:
        print(f"Failed to get weather data: {weather_data}")
