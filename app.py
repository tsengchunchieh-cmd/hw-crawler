import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("可編輯天氣資料展示")

# 1️⃣ 讀取資料
df = pd.read_csv("data.csv")  # 假設你的資料有 'obs_time' 與 'temperature' 欄位

# 2️⃣ 顯示原始資料
st.subheader("原始資料")
st.dataframe(df)

# 3️⃣ 可編輯資料 - 用手動輸入方式
st.subheader("編輯資料")
edited_rows = []

for i, row in df.iterrows():
    st.write(f"第 {i+1} 筆資料")
    obs_time = st.text_input(f"時間 (obs_time) {i+1}", value=row['obs_time'], key=f"time_{i}")
    temperature = st.number_input(f"溫度 (temperature) {i+1}", value=float(row['temperature']), key=f"temp_{i}")
    edited_rows.append({'obs_time': obs_time, 'temperature': temperature})

# 轉成新的 DataFrame
df_edited = pd.DataFrame(edited_rows)
df_edited["ObsTime"] = pd.to_datetime(df_edited["obs_time"])  # 轉成時間格式

# 4️⃣ 畫圖
st.subheader("溫度折線圖")
st.line_chart(df_edited.set_index("ObsTime")["temperature"], width='stretch')

# 5️⃣ 可選：顯示修改後的完整表格
st.subheader("修改後的完整資料")
st.dataframe(df_edited)
