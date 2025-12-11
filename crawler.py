import requests
import json
import sqlite3
import datetime
from typing import Union, Dict, Any, List 
import urllib3 # 導入 urllib3

# 禁用 requests 在 verify=False 時發出的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
DATABASE_NAME = "weather_data.db"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001" 

# --- Initialization Logic ---
def init_db():
    """
    Initializes the SQLite database: creates the file and the necessary table.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                fetch_timestamp TEXT NOT NULL,
                location_count INTEGER,
                raw_data TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print(f"Database '{DATABASE_NAME}' initialized successfully.")
    except sqlite3.Error as e:
        print(f"FATAL DB ERROR during initialization: {e}")

# --- Fetching Logic ---
def get_weather_data(api_key: str) -> Union[Dict[str, Any], str]:
    """
    Fetches weather data from an external CWA-like API.
    """
    params = {
        'Authorization': api_key,
        'format': 'JSON',
        'locationName': '臺北市' 
    }

    try:
        # 【關鍵修正】: 啟用 verify=False 繞過 SSL 憑證錯誤
        # 【修正已完成】
        response = requests.get(API_URL, params=params, timeout=10, verify=False) 
        response.raise_for_status() 

        data = response.json()

        if 'success' in data and data['success'] == 'false':
            return f"API Error: {data.get('message', 'Unknown API failure')}"

        return data

    except requests.exceptions.HTTPError as errh:
        # 處理 API 金鑰失效的常見錯誤碼
        if response.status_code in [401, 403]:
            return "Unauthorized or Forbidden: Check your API key. (Key might be invalid or expired)"
        return f"HTTP Error: {errh}"
    except requests.exceptions.RequestException as err:
        return f"An unexpected request error occurred: {err}"
    except json.JSONDecodeError:
        return "Failed to decode JSON response from the API."

# --- Persistence Logic (Save) ---
def save_to_db(data: Dict[str, Any]) -> str:
    """
    Saves the fetched weather data into the SQLite database.
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()

            dataset_id = data.get("records", {}).get("datasetDescription", "unknown_dataset")
            fetch_time = datetime.datetime.now().isoformat()
            location_count = len(data["records"]["location"])
            raw_data_json = json.dumps(data)

            cursor.execute("""
                INSERT INTO weather_records 
                (dataset_id, fetch_timestamp, location_count, raw_data) 
                VALUES (?, ?, ?, ?)
            """, (dataset_id, fetch_time, location_count, raw_data_json))

            conn.commit()
        
        return f"Successfully saved {location_count} records for dataset '{dataset_id}' to SQLite."

    except sqlite3.Error as e:
        return f"Database Error: Failed to save data to SQLite: {e}"

# --- Retrieval Logic (Read) ---
def get_history_from_db(limit: int = 10) -> Union[List[Dict[str, Any]], str]:
    """
    Retrieves the most recent weather records from the SQLite database.
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, dataset_id, fetch_timestamp, location_count, raw_data 
                FROM weather_records 
                ORDER BY fetch_timestamp DESC 
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
        
        # Convert sqlite3.Row objects to standard Python dictionaries
        history_list = [dict(row) for row in rows]
        
        # Parse the raw_data JSON string back into a dictionary
        for record in history_list:
            try:
                record['raw_data'] = json.loads(record['raw_data'])
            except json.JSONDecodeError:
                record['raw_data'] = {"error": "Corrupted JSON data in DB"}

        return history_list

    except sqlite3.Error as e:
        return f"Database Error: Failed to retrieve history from SQLite: {e}"

# --- Main Execution Example ---
if __name__ == "__main__":
    # 【金鑰更新完成】: 使用您提供的金鑰
    # 請注意：此金鑰 CWA-F1411072-444D-4D41-B919-FA689356B3E7 可能仍需更新為最新的
    YOUR_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7" 

    init_db()
    
    print("\n--- 1. 執行資料抓取 (使用 verify=False) ---")
    weather_data = get_weather_data(YOUR_API_KEY)

    if isinstance(weather_data, dict):
        print(f"✅ 資料抓取成功。總共 {len(weather_data['records']['location'])} 筆地點資料。")
        
        print("\n--- 2. 儲存資料至資料庫 ---")
        save_result = save_to_db(weather_data)
        print(save_result)
        
        print("\n--- 3. 讀取歷史資料 ---")
        history = get_history_from_db(limit=1)
        if isinstance(history, list) and history:
            print(f"✅ 成功從資料庫讀取 {len(history)} 筆記錄。")
            print(f"最新記錄的時間: {history[0]['fetch_timestamp']}")
        elif isinstance(history, str):
             print(f"❌ 讀取歷史資料失敗: {history}")

    else:
        print(f"❌ 資料抓取失敗: {weather_data}")
