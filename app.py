# app_incremental.py
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import sqlite3
from pathlib import Path

st.set_page_config(page_title="氣象資料即時顯示 (增量版)", layout="wide")

DB_FILE = "weather_data.db"

# -------------------------
# 1️⃣ 建立 SQLite 資料庫
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            location TEXT,
            startTime TEXT,
            endTime TEXT,
            temperature REAL,
            PRIMARY KEY(location, startTime)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------------
# 2️⃣ 抓取 API 資料
# -------------------------
API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7"
API_URL = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001?Authorization={API_KEY}&downloadType=WEB&format=JSON"

@st.cache_data(ttl=3600)
def fetch_weather():
    response = requests.get(API_URL)
    data = response.json()
    records = []
    for loc in data['cwbopendata']['dataset']['locations']['location']:
        location_name = loc['locationName']
        for element in loc['weatherElement']:
            if element['elementName'] == 'TEMP':
                for time_slot in element['time']:
                    records.append({
                        'location': location_name,
                        'startTime': time_slot['startTime'],
                        'endTime': time_slot['endTime'],
                        'temperature': float(time_slot['elementValue'][0]['value'])
                    })
    return pd.DataFrame(records)

# -------------------------
# 3️⃣ 將資料增量存入 SQLite
# -------------------------
def save_incremental(df):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in df.iterrows():
        try:
            c.execute('''
                INSERT OR IGNORE INTO weather (location, startTime, endTime, temperature)
                VALUES (?, ?, ?, ?)
            ''', (row['location'], row['startTime'], row['endTime'], row['temperature']))
        except Exception as e:
            st.error(f"儲存資料錯誤: {e}")
    conn.commit()
    conn.close()

# -------------------------
# 4️⃣ 讀取 SQLite 資料
# -------------------------
conn = sqlite3.connect(DB_FILE)
df_db = pd.read_sql("SELECT * FROM weather", conn)
conn.close()

# 如果資料庫是空的，抓 API
if df_db.empty:
    df_temp = fetch_weather()
    save_incremental(df_temp)
    df_db = df_temp.copy()
else:
    df_temp = fetch_weather()
    save_incremental(df_temp)
    conn = sqlite3.connect(DB_FILE)
    df_db = pd.read_sql("SELECT * FROM weather", conn)
    conn.close()

# -------------------------
# 5️⃣ Streamlit UI
# -------------------------
st.title("🌤 氣象資料即時顯示 (增量版)")

# 側邊欄選地區與時間
df_db['startTime'] = pd.to_datetime(df_db['startTime'])
locations = df_db['location'].unique().tolist()
selected_locations = st.sidebar.multiselect("選擇地區", options=locations, default=locations[:3])

min_time, max_time = df_db['startTime'].min(), df_db['startTime'].max()
selected_time = st.sidebar.slider("選擇時間範圍", min_value=min_time, max_value=max_time, value=(min_time, max_time))

# 過濾資料
df_filtered = df_db[
    (df_db['location'].isin(selected_locations)) &
    (df_db['startTime'] >= selected_time[0]) &
    (df_db['startTime'] <= selected_time[1])
]

st.subheader("📋 溫度資料預覽")
st.dataframe(df_filtered)

# 繪圖
st.subheader("🌡 溫度走勢圖")
plt.figure(figsize=(12, 6))
for loc in selected_locations:
    df_loc = df_filtered[df_filtered['location'] == loc]
    plt.plot(df_loc['startTime'], df_loc['temperature'], marker='o', label=loc)

plt.xlabel("時間")
plt.ylabel("溫度 (°C)")
plt.title("各地區溫度走勢")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(plt)
