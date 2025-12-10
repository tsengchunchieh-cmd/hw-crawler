from flask import Flask, jsonify, request
from flask_cors import CORS
from crawler import get_weather_data

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

@app.route('/api/weather', methods=['GET'])
def weather():
    """
    API endpoint to get weather data.
    The CWA API key must be passed as a query parameter.
    e.g., /api/weather?api_key=YOUR_API_KEY
    """
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({"error": "API key is required"}), 400

    data = get_weather_data(api_key)
    if isinstance(data, str):
        return jsonify({"error": data}), 500
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
