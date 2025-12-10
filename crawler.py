# crawler.py
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_FILE = "weather.db"

def get_weather_data(api_key: str):
    """
    取得 CWA 天氣資料，整理成 dict 並存入 SQLite
    """
    if not api_key:
        return "API Key not provided", None

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {"Authorization": api_key, "format": "JSON"}

    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data_json = resp.json()

        records = []
        result_dict = {}

        for loc in data_json.get("records", {}).get("location", []):
            name = loc.get("locationName")
            elements = {el["elementName"]: el["elementValue"]["value"]
                        for el in loc.get("weatherElement", [])}
            result_dict[name] = elements

            obs_time = loc.get("time", {}).get("obsTime", datetime.utcnow().isoformat())
            records.append((name, elements.get("MinT"), elements.get("MaxT"), obs_time))

        # 存入 SQLite
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT,
                min_temp REAL,
                max_temp REAL,
                obs_time TEXT
            )
        """)
        c.executemany("""
            INSERT INTO weather (location, min_temp, max_temp, obs_time)
            VALUES (?, ?, ?, ?)
        """, records)
        conn.commit()
        conn.close()

        # DataFrame
        df = pd.DataFrame(records, columns=["location", "MinT", "MaxT", "ObsTime"])
        df = df.sort_values(by="ObsTime", ascending=False).reset_index(drop=True)

        return result_dict, df

    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e}", None
    except Exception as e:
        return f"Error fetching data: {e}", None
