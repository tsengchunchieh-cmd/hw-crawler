from flask import Flask, jsonify, request
from flask_cors import CORS
from crawler import get_weather_data, save_to_db

app = Flask(__name__)
CORS(app)

DEFAULT_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7"

@app.route('/api/weather', methods=['GET'])
def weather():
    api_key = request.args.get('api_key', DEFAULT_API_KEY)
    data = get_weather_data(api_key)
    if isinstance(data, str):
        return jsonify({"error": data}), 500

    save_msg = save_to_db(data)
    return jsonify({"status": "ok", "message": save_msg, "records_count": len(data["records"]["location"])})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
