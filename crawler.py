# crawler.py
import requests
import sqlite3
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_FILE = "weather.db"

def get_weather_data(api_key):
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {"Authorization": api_key, "format": "JSON"}

    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return f"Error fetching data: {e}"

def save_to_db(data):
    if "records" not in data:
        return "No records found"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 建立資料表
    c.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        weather TEXT,
        min_temp REAL,
        max_temp REAL,
        obs_time TEXT
    )
    """)

    # 插入資料
    for loc in data["records"]["location"]:
        name = loc.get("locationName")
        weather = loc["weatherElement"][0]["elementValue"]["value"]
        min_temp = float(loc["weatherElement"][2]["elementValue"]["value"])
        max_temp = float(loc["weatherElement"][4]["elementValue"]["value"])
        obs_time = loc["time"]["obsTime"]

        c.execute("""
        INSERT INTO weather (location, weather, min_temp, max_temp, obs_time)
        VALUES (?, ?, ?, ?, ?)
        """, (name, weather, min_temp, max_temp, obs_time))

    conn.commit()
    conn.close()
    return "Data saved successfully"
