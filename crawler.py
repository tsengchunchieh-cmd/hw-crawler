import requests
import json
import sqlite3
import datetime
from typing import Union, Dict, Any, List 
import urllib3

# 禁用 requests 在 verify=False 時發出的警告 (解決 SSL 錯誤的副作用)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
DATABASE_NAME = "weather_data.db"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001" 
# 【已更新金鑰】: 請注意此金鑰可能已失效，若失敗請更換新的金鑰
YOUR_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7" 

# --- Initialization Logic ---
def init_db():
    """
    Initializes the SQLite database: creates the file and the necessary table.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
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
        # 【關鍵修正】: 加入 verify=False 繞過 SSL 憑證錯誤
        response = requests.get(API_URL, params=params, timeout=10, verify=False) 
        response.raise_for_status() 

        data = response.json()

        if 'success' in data and data['success'] == 'false':
            return f"API Error: {data.get('message', 'Unknown API failure')}"

        return data

    except requests.exceptions.HTTPError as errh:
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

# --- Display/Parse Logic ---
def parse_weather_forecast(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses the CWA F-C0032-001 (36-hour forecast) JSON data 
    for the specified location (臺北市) and extracts key elements 
    for each 12-hour period.
    """
    forecasts = []
    
    try:
        # 由於我們只請求臺北市，所以 location 陣列只有一個元素 [0]
        location = data['records']['location'][0]
        location_name = location['locationName']
        weather_elements = location['weatherElement']
        
        # 將所有氣象要素轉換為以 'elementName' 為鍵的字典，方便查詢
        element_map = {
            elem['elementName']: elem['time'] 
            for elem in weather_elements
        }
        
        # 預報資料以 Wx (天氣現象) 的時間為準，共有三期 (36小時 / 12小時一期)
        if 'Wx' in element_map:
            wx_times = element_map['Wx']
            
            for period in wx_times:
                start_time = period['startTime']
                
                # 提取天氣現象 (Wx)
                weather_description = period['elementValue'][0]['value']
                
                # 提取降雨機率 (PoP)
                pop_value = next((
                    t['elementValue'][0]['value'] 
                    for t in element_map.get('PoP', []) 
                    if t['startTime'] == start_time
                ), 'N/A')
                
                # 提取最低溫度 (MinT)
                min_t = next((
                    t['elementValue'][0]['value'] 
                    for t in element_map.get('MinT', []) 
                    if t['startTime'] == start_time
                ), 'N/A')

                # 提取最高溫度 (MaxT)
                max_t = next((
                    t['elementValue'][0]['value'] 
                    for t in element_map.get('MaxT', []) 
                    if t['startTime'] == start_time
                ), 'N/A')
                
                forecasts.append({
                    'Location': location_name,
                    'StartTime': start_time,
                    'EndTime': period['endTime'],
                    'Weather': weather_description,
                    'PoP (%)': pop_value,
                    'Min Temp (°C)': min_t,
                    'Max Temp (°C)': max_t,
                })

    except Exception as e:
        print(f"Error during data parsing: {e}")
        return []
        
    return forecasts

# --- Main Execution Example ---
if __name__ == "__main__":
    
    # 使用您提供的金鑰
    api_key_to_use = YOUR_API_KEY 

    init_db()
    
    print("\n--- 1. 執行資料抓取 (使用 verify=False) ---")
    weather_data = get_weather_data(api_key_to_use)

    if isinstance(weather_data, dict):
        print(f"✅ 資料抓取成功。總共 {len(weather_data['records']['location'])} 筆地點資料。")
        
        print("\n--- 2. 儲存資料至資料庫 ---")
        save_result = save_to_db(weather_data)
        print(save_result)
        
        # 新增解析步驟：
        print("\n--- 3. 解析並顯示預報資料 ---")
        parsed_forecast = parse_weather_forecast(weather_data)
        
        if parsed_forecast:
            print(f"成功解析 {len(parsed_forecast)} 個 12 小時預報期:")
            for item in parsed_forecast:
                print("--------------------------------------------------")
                print(f"地區: {item['Location']}")
                print(f"時段: {item['StartTime']} ~ {item['EndTime']}")
                print(f"天氣: {item['Weather']}")
                print(f"溫度: {item['Min Temp (°C)']}°C ~ {item['Max Temp (°C)']}°C")
                print(f"降雨機率(PoP): {item['PoP (%)']}%")
            print("--------------------------------------------------")
        else:
            print("❌ 資料解析失敗或無預報資料。")

    else:
        print(f"❌ 資料抓取失敗: {weather_data}")
