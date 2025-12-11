from flask import Flask, jsonify, request
from flask_cors import CORS
# 導入所有的 crawler 函數 (新增 parse_weather_forecast)
from crawler import get_weather_data, save_to_db, init_db, get_history_from_db, parse_weather_forecast 

app = Flask(__name__)
# 啟用 CORS 支援，允許跨域請求
CORS(app)

# 使用中央氣象署的預設開放資料 API Key
# 注意：此金鑰 CWA-F1411072-444D-4D41-B919-FA689356B3E7 已確認可連線，但可能隨時失效
DEFAULT_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7"

# --- API 1: 獲取、儲存並回傳解析後的數據 ---
@app.route('/api/weather', methods=['GET'])
def weather():
    api_key = request.args.get('api_key', DEFAULT_API_KEY)
    
    # 1. 獲取資料 (已包含 verify=False 修正)
    data = get_weather_data(api_key)
    
    # 處理抓取錯誤
    if isinstance(data, str):
        # 假設錯誤字串包含權限問題 (401/403) 或服務問題 (500)
        status_code = 401 if "Unauthorized" in data or "Forbidden" in data else 500
        # 額外紀錄錯誤，幫助除錯
        print(f"Fetch Error: {data}")
        return jsonify({"error": data}), status_code

    # 2. 儲存到資料庫
    save_msg = save_to_db(data)
    
    # 處理儲存錯誤
    if save_msg.startswith("Database Error:"):
        print(f"Database Save Error: {save_msg}")
        return jsonify({"status": "error", "message": save_msg}), 500
        
    # 3. 解析資料並回傳結構化的預報
    parsed_forecast = parse_weather_forecast(data) # <-- 【修正點】: 呼叫解析函式

    return jsonify({
        "status": "ok", 
        "message": save_msg, 
        "records_count": len(parsed_forecast), # 回傳解析後記錄數
        "forecast": parsed_forecast # <-- 【修正點】: 回傳預報資料
    })


# --- API 2: 檢索歷史數據 ---
@app.route('/api/history', methods=['GET'])
def history():
    # 從 URL 參數獲取 limit，預設為 5
    try:
        limit = int(request.args.get('limit', 5))
        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100."}), 400
    except ValueError:
        return jsonify({"error": "Invalid value for 'limit' parameter."}), 400

    # 從資料庫檢索數據
    history_data = get_history_from_db(limit)
    
    # 處理檢索錯誤
    if isinstance(history_data, str) and history_data.startswith("Database Error:"):
        print(f"Database Retrieve Error: {history_data}")
        return jsonify({"status": "error", "message": history_data}), 500

    # 返回歷史記錄
    # 備註: history_data 中的 raw_data 仍為 JSON 格式，若需要解析，
    # 則需在迴圈中對每筆記錄的 raw_data 執行 parse_weather_forecast
    return jsonify({
        "status": "ok",
        "count": len(history_data),
        "records": history_data
    })


if __name__ == "__main__":
    # 在應用程式啟動前初始化資料庫
    init_db() 
    # 移除 use_reloader=False 讓開發過程更順暢，除非在生產環境中遇到特殊問題
    app.run(host="0.0.0.0", port=5001, debug=True) # 啟用 debug=True，方便開發
