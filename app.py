# app.py
import streamlit as st
import pandas as pd
import requests
import sqlite3
import urllib3

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001?Authorization=CWA-F1411072-444D-4D41-B919-FA689356B3E7&downloadType=WEB&format=JSON"

DB_FILE = "weather_data.db"

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            location TEXT,
            obs_time TEXT,
            temperature REAL,
            PRIMARY KEY(location, obs_time)
        )
    ''')
    conn.commit()
    conn.close()

# 抓取天氣資料
@st.cache_data
def fetch_weather():
    try:
        response = requests.get(API_URL, verify=False)  # 關閉 SSL 驗證
        data = response.json()
        records = []
        for location in data['cwbopendata']['dataset']['location']:
            loc_name = location['locationName']
            for weather_element in location['weatherElement']:
                if weather_element['elementName'] == 'TEMP':
                    for obs in weather_element['time']:
                        records.append({
                            "location": loc_name,
                            "obs_time": obs['startTime'],
                            "temperature": float(obs['elementValue'][0]['value'])
                        })
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        st.error(f"抓取資料失敗: {e}")
        return pd.DataFrame()

# 存進 SQLite
def save_to_db(df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql("weather", conn, if_exists="replace", index=False)
    conn.close()

# 主程式
def main():
    st.title("天氣資料抓取與顯示")
    
    init_db()  # 初始化資料庫
    
    if st.button("抓取最新資料"):
        df = fetch_weather()
        if not df.empty:
            save_to_db(df)
            st.success("資料已更新到 SQLite！")
            st.dataframe(df)
        else:
            st.warning("沒有資料被抓到。")
    
    # 顯示現有資料
    conn = sqlite3.connect(DB_FILE)
    df_db = pd.read_sql("SELECT * FROM weather", conn)
    conn.close()
    
    if not df_db.empty:
        st.subheader("SQLite 現有資料")
        st.dataframe(df_db)
    else:
        st.info("資料庫目前是空的")

if __name__ == "__main__":
    main()

