# crawler.py
import requests
import urllib3

# 關閉 SSL 憑證警告（CWA 憑證有問題，必要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_weather_data(api_key):
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

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"


