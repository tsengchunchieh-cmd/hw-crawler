# crawler.py

import requests
import urllib3
# 為了讓回傳型別更清晰
from typing import Union, Dict, Any 

# 關閉 SSL 憑證警告（CWA 憑證有問題，必要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_weather_data(api_key: str) -> Union[Dict[str, Any], str]:
    """
    從 CWA API 獲取天氣資料，並處理 SSL 和常見 HTTP 錯誤。
    """
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

    params = {
        "Authorization": api_key,
        "format": "JSON"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
            verify=False  # ⭐⭐⭐ 關鍵：關閉 SSL 驗證
        )

        # 如果狀態碼非 200-299，則拋出 requests.exceptions.HTTPError
        response.raise_for_status() 

        # 嘗試解析 JSON
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            # 處理伺服器回傳非 JSON 格式的情況（極少見，但為安全起見）
            return f"Error: Failed to decode JSON. Response text: {response.text[:100]}..."

    except requests.exceptions.HTTPError as e:
        # 處理 HTTP 錯誤（例如 401, 403, 404, 500 等）
        status_code = response.status_code
        if status_code in [401, 403]:
            # 專門提示金鑰失效或無權限
            return f"Error fetching data: API Key Unauthorized or Forbidden ({status_code})."
        else:
            return f"Error fetching data: HTTP Error {status_code} ({e})"

    except requests.exceptions.RequestException as e:
        # 處理其他網路相關錯誤 (例如連線超時、DNS 錯誤等)
        return f"Error fetching data: Connection or network issue ({e})"
