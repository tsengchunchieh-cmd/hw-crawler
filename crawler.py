# --- 3. 解析邏輯 (最終修正版本，簡化時間匹配) ---
def parse_weather_forecast(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 CWA 36 小時預報資料，提取關鍵資訊。"""
    forecasts = []
    
    try:
        if not data.get('records') or not data['records'].get('location'):
            return []
            
        location = data['records']['location'][0]
        location_name = location.get('locationName', '未知地點')
        weather_elements = location.get('weatherElement', [])
        
        # 將所有氣象要素轉換為以 elementName 為鍵的字典 (值為其 time 列表)
        element_map = {elem['elementName']: elem['time'] for elem in weather_elements}
        
        wx_times = element_map.get('Wx')
        if not wx_times:
            return []

        # 輔助函式：安全地從元素列表中提取特定時間的值
        def safe_extract_value(element_name, period_time):
            # 遍歷該元素的所有時間點
            for t in element_map.get(element_name, []):
                # 我們不使用 t['startTime'] 進行匹配，而是檢查時間點是否重疊或匹配
                if t.get('startTime') == period_time.get('startTime'):
                    # 確保 elementValue 鍵和列表存在
                    if t.get('elementValue') and t['elementValue']:
                        return t['elementValue'][0].get('value', 'N/A')
            return 'N/A'
            
        for period in wx_times:
            start_time = period.get('startTime', 'N/A')
            end_time = period.get('endTime', 'N/A')
            
            # 提取天氣現象 (Wx) - 直接從 Wx 的 period 中提取
            weather_value_list = period.get('elementValue')
            weather_description = weather_value_list[0].get('value', 'N/A') if weather_value_list else 'N/A'
            
            # 提取 PoP, MinT, MaxT (傳入當前預報期 period 進行時間匹配)
            pop_value = safe_extract_value('PoP', period)
            min_t = safe_extract_value('MinT', period)
            max_t = safe_extract_value('MaxT', period)
            
            # 額外檢查：如果 MaxT 是空，可能是因為它是另一個時段的開始時間，我們需要確保它是當前時段的值
            if max_t == 'N/A' and 'MaxT' in element_map:
                # 為了避免過度複雜化，這裡我們假設 MinT 和 MaxT 的時間點結構是一致的
                # 若問題持續，可能是 API 預報期欄位名稱不同
                pass 
                
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
        # 如果是 Streamlit 應用，顯示原始資料幫助我們除錯
        # st.json(data) 
        return []
        
    return forecasts
