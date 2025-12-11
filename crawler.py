import streamlit as st
import pandas as pd
import requests
import json
import sqlite3
import datetime
import urllib3
from typing import Union, Dict, Any, List 

# 關閉 SSL 憑證警告（CWA 憑證問題的必要修正）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
DATABASE_NAME = "weather_data.db"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001" 
# 【已更新金鑰】: 請確認此金鑰 CWA-F1411072-444D-4D41-B919-FA689356B3E7 有效
DEFAULT_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7" 
DEFAULT_LOCATION = '臺北市'

# --- 1. 資料庫邏輯 (從 crawler.py 繼承) ---
def init_db():
    """初始化 SQLite 資料庫。"""
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
        # Streamlit 應用中不適合在每次執行時都輸出 print，改為 st.info
        # st.info(f"Database '{DATABASE_NAME}' initialized successfully.")
    except sqlite3.Error as e:
        st.error(f"FATAL DB ERROR during initialization: {e}")

def save_to_db(data: Dict[str, Any]) -> str:
    """將抓取的資料儲存至資料庫。"""
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

def get_history_from_db(limit: int = 10) -> Union[List[Dict[str, Any]], str]:
    """從資料庫檢索歷史記錄。"""
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
            
            history_list = [dict(row) for row in rows]
            
            # 將 raw_data JSON 欄位解碼
            for record in history_list:
                try:
                    record['raw_data'] = json.loads(record['raw_data'])
                except json.JSONDecodeError:
                    record['raw_data'] = {"error": "Corrupted JSON data in DB"}

            return history_list
    except sqlite3.Error as e:
        return f"Database Error: Failed to retrieve history from SQLite: {e}"

# --- 2. 爬蟲邏輯 (從 crawler.py 繼承) ---
def get_weather_data(api_key: str, location: str) -> Union[Dict[str, Any], str]:
    """獲取 CWA 天氣資料，包含 SSL 修正。"""
    params = {
        'Authorization': api_key,
        'format': 'JSON',
        'locationName': location 
    }

    try:
        # 關鍵修正：verify=False
        response = requests.get(API_URL, params=params, timeout=15, verify=False) 
        response.raise_for_status() 
        
        data = response.json()
        if 'success' in data and data['success'] == 'false':
            return f"API Error: {data.get('message', 'Unknown API failure')}"

        return data

    except requests.exceptions.HTTPError as errh:
        if response.status_code in [401, 403]:
            return f"Unauthorized or Forbidden: Check your API key ({response.status_code})."
        return f"HTTP Error: {errh}"
    except requests.exceptions.RequestException as err:
        return f"An unexpected request error occurred: {err}"
    except json.JSONDecodeError:
        return "Failed to decode JSON response from the API."

# --- 3. 解析邏輯 (從 crawler.py 繼承) ---
def parse_weather_forecast(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 CWA 36 小時預報資料，提取關鍵資訊。"""
    forecasts = []
    try:
        location = data['records']['location'][0]
        location_name = location['locationName']
        weather_elements = location['weatherElement']
        
        element_map = {elem['elementName']: elem['time'] for elem in weather_elements}
        
        if 'Wx' in element_map:
            wx_times = element_map['Wx']
            
            for period in wx_times:
                start_time = period['startTime']
                
                weather_description = period['elementValue'][0]['value']
                
                # 提取 PoP, MinT, MaxT (使用 next() 處理找不到的情況)
                pop_value = next((t['elementValue'][0]['value'] for t in element_map.get('PoP', []) if t['startTime'] == start_time), 'N/A')
                min_t = next((t['elementValue'][0]['value'] for t in element_map.get('MinT', []) if t['startTime'] == start_time), 'N/A')
                max_t = next((t['elementValue'][0]['value'] for t in element_map.get('MaxT', []) if t['startTime'] == start_time), 'N/A')
                
                forecasts.append({
                    'Location': location_name,
                    'Start Time': start_time,
                    'End Time': period['endTime'],
                    'Weather': weather_description,
                    'PoP (%)': pop_value,
                    'Min Temp (°C)': min_t,
                    'Max Temp (°C)': max_t,
                })

    except Exception as e:
        st.warning(f"資料解析發生錯誤: {e}")
        return []
        
    return forecasts

# --- 4. Streamlit 應用介面 ---
st.set_page_config(page_title="CWA 天氣資料抓取與分析", layout="wide")
st.title("🇹🇼 CWA 天氣資料即時抓取與歷史記錄")

# 確保資料庫在應用程式啟動時初始化
init_db() 

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ API 設定")
    api_key_input = st.text_input("API Key (CWA)", value=DEFAULT_API_KEY, type="password")
    location_input = st.text_input("地點名稱", value=DEFAULT_LOCATION)
    
    st.subheader("📚 歷史記錄查詢")
    history_limit = st.slider("顯示記錄筆數", min_value=1, max_value=50, value=5)

# --- 主應用區塊 ---

st.header("即時天氣預報抓取")
if st.button("🚀 抓取最新 36 小時天氣預報"):
    # 使用 Streamlit 內建的 spinner 顯示載入狀態
    with st.spinner(f'正在抓取 {location_input} 的資料...'):
        
        # 執行抓取
        weather_data = get_weather_data(api_key_input, location_input)

        if isinstance(weather_data, dict):
            st.success("✅ 資料抓取成功！")
            
            # 儲存資料
            save_msg = save_to_db(weather_data)
            st.info(save_msg)
            
            # 解析並顯示預報
            parsed_forecast = parse_weather_forecast(weather_data)
            
            if parsed_forecast:
                df = pd.DataFrame(parsed_forecast)
                st.subheader(f"最新預報：{location_input} ({len(parsed_forecast)} 個時段)")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("資料解析失敗或預報格式不正確。")
        else:
            st.error(f"❌ 資料抓取失敗: {weather_data}")

# --- 歷史資料顯示區塊 ---
st.divider()
st.header("歷史抓取記錄")

history_data = get_history_from_db(history_limit)

if isinstance(history_data, str) and history_data.startswith("Database Error:"):
    st.error(f"❌ 歷史資料檢索失敗: {history_data}")
elif history_data:
    st.info(f"顯示最近 {len(history_data)} 筆記錄。")
    
    # 建立一個包含關鍵資訊的 DataFrame
    history_df_list = []
    for record in history_data:
        history_df_list.append({
            "ID": record["id"],
            "抓取時間": record["fetch_timestamp"],
            "資料集描述": record["raw_data"]["records"]["datasetDescription"],
            "地點數": record["location_count"],
        })
    
    st.dataframe(pd.DataFrame(history_df_list), use_container_width=True)
    
    # 選項：展開查看原始 JSON
    if st.checkbox("展開原始 JSON 資料"):
        selected_id = st.selectbox("選擇要查看的記錄 ID", [r["id"] for r in history_data])
        raw_record = next(r for r in history_data if r["id"] == selected_id)
        st.json(raw_record["raw_data"])

else:
    st.info("資料庫中尚無歷史記錄。")
