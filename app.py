from flask import Flask, jsonify, request
from flask_cors import CORS
# 導入所有的 crawler 函數
from crawler import get_weather_data, save_to_db, init_db, get_history_from_db 

app = Flask(__name__)
CORS(app)

# 使用中央氣象署的預設開放資料 API Key
DEFAULT_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7"

# --- API 1: 獲取並儲存天氣數據 ---
@app.route('/api/weather', methods=['GET'])
def weather():
    api_key = request.args.get('api_key', DEFAULT_API_KEY)
    data = get_weather_data(api_key)
    
    # 處理抓取錯誤
    if isinstance(data, str):
        # 假設錯誤字串包含權限問題 (401/403) 或服務問題 (500)
        status_code = 401 if "Unauthorized" in data or "Forbidden" in data else 500
        return jsonify({"error": data}), status_code

    # 儲存到資料庫
    save_msg = save_to_db(data)
    
    # 處理儲存錯誤
    if save_msg.startswith("Database Error:"):
        return jsonify({"status": "error", "message": save_msg}), 500
        
    return jsonify({
        "status": "ok", 
        "message": save_msg, 
        "records_count": len(data["records"]["location"])
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
        return jsonify({"status": "error", "message": history_data}), 500

    # 返回歷史記錄
    return jsonify({
        "status": "ok",
        "count": len(history_data),
        "records": history_data
    })


if __name__ == "__main__":
    # 在應用程式啟動前初始化資料庫
    init_db() 
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
