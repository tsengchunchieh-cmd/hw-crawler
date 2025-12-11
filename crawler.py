# --- 3. 解析邏輯 (修正後的版本) ---
def parse_weather_forecast(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 CWA 36 小時預報資料，提取關鍵資訊。"""
    forecasts = []
    
    try:
        # 確保 location 陣列存在且不為空
        if not data.get('records') or not data['records'].get('location'):
            st.error("API 回傳資料結構異常：缺少 'records' 或 'location' 欄位。")
            return []
            
        location = data['records']['location'][0]
        location_name = location.get('locationName', '未知地點')
        weather_elements = location.get('weatherElement', [])
        
        # 將所有氣象要素轉換為以 elementName 為鍵的字典 (值為其 time 列表)
        element_map = {elem['elementName']: elem['time'] for elem in weather_elements}
        
        # 預報資料以 Wx (天氣現象) 的時間為準
        wx_times = element_map.get('Wx')
        if not wx_times:
            st.warning("資料中缺少 'Wx' (天氣現象) 元素，無法解析預報時段。")
            return []
            
        # 輔助函式：安全地從元素列表中提取特定時間的值
        def safe_extract_value(element_name, period_time):
            # 遍歷該元素的所有時間點
            for t in element_map.get(element_name, []):
                # 我們只檢查 start_time 是否匹配，這是最常見的匹配點
                if t.get('startTime') == period_time.get('startTime'):
                    # 確保 elementValue 鍵和列表存在
                    if t.get('elementValue') and t['elementValue']:
                        # 這裡是修正的關鍵：確保我們能安全地獲取 value
                        return t['elementValue'][0].get('value', 'N/A')
            return 'N/A'
            
        for period in wx_times:
            start_time = period.get('startTime', 'N/A')
            end_time = period.get('endTime', 'N/A')

            # 提取天氣現象 (Wx) - Wx 的值可以直接從 period 自身提取
            weather_value_list = period.get('elementValue')
            # 修正點：安全存取
            weather_description = weather_value_list[0].get('value', 'N/A') if weather_value_list else 'N/A'
            
            # 提取 PoP, MinT, MaxT
            # 使用當前的 period 來匹配時間
            pop_value = safe_extract_value('PoP', period)
            min_t = safe_extract_value('MinT', period)
            max_t = safe_extract_value('MaxT', period)
            
            forecasts.append({
                'Location': location_name,
                'Start Time': start_time,
                'End Time': end_time,
                'Weather': weather_description,
                'PoP (%)': pop_value,
                'Min Temp (°C)': min_t,
                'Max Temp (°C)': max_t,
            })

    except Exception as e:
        st.error(f"資料解析發生未預期錯誤: {e}")
        return []
        
    return forecasts
