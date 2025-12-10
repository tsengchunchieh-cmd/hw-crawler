# Taiwan Weather Map

This project displays a dynamic map of Taiwan with temperature forecasts for various locations.

## Tech Stack
- Python
- Flask
- Streamlit (for the original app)
- HTML
- JavaScript
- Tailwind CSS

## Getting Started

### Prerequisites
- Python 3.x
- pip

### Installation
1. Clone the repo (if you haven't already).
2. Install the Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

There are two parts to this project: the original Streamlit app and the new dynamic map.

### Dynamic Map (HTML/JS/Flask)

1.  **Start the backend server:**
    Open a terminal and run the following command to start the Flask server. This will serve the weather data at `http://127.0.0.1:5001`.
    ```sh
    python server.py
    ```

2.  **Open the map:**
    Open the `index.html` file in your web browser.

3.  **Load the weather data:**
    You will see an input field to enter your CWA (Central Weather Administration) API key. You can get a free key from the [CWA Open Data Platform](https://opendata.cwa.gov.tw/user/authkey).
    Enter your API key and click the "Load Weather" button. The map will then display the latest temperature forecasts for major cities.

### Original Streamlit App

To run the original Streamlit application:
```sh
streamlit run app.py
```

## How the Dynamic Map Works

-   The `server.py` file runs a Flask web server that exposes a `/api/weather` endpoint. This endpoint fetches weather data using the `crawler.py` module.
-   The `index.html` file contains a simplified SVG map of Taiwan.
-   The JavaScript code in `index.html` sends a request to the Flask server, retrieves the weather data, and then dynamically updates the SVG map to display the temperatures for each city.
-   Tailwind CSS is used for styling the `index.html` page.