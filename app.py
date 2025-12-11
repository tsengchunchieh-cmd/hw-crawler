from flask import Flask, jsonify, request
from flask_cors import CORS
# Add get_history_from_db to the import
from crawler import get_weather_data, save_to_db, init_db, get_history_from_db 

app = Flask(__name__)
CORS(app)

DEFAULT_API_KEY = "CWA-F1411072-444D-4D41-B919-FA689356B3E7"

# --- Existing /api/weather route (Unchanged) ---
@app.route('/api/weather', methods=['GET'])
def weather():
    # ... (Your existing weather logic) ...
    api_key = request.args.get('api_key', DEFAULT_API_KEY)
    data = get_weather_data(api_key)
    if isinstance(data, str):
        return jsonify({"error": data}), 500

    save_msg = save_to_db(data)
    if save_msg.startswith("Database Error:"):
        return jsonify({"status": "error", "message": save_msg}), 500
        
    return jsonify({"status": "ok", "message": save_msg, "records_count": len(data["records"]["location"])})


# --- New /api/history route ---
@app.route('/api/history', methods=['GET'])
def history():
    # Get the desired number of records from the query parameter, defaulting to 5
    try:
        limit = int(request.args.get('limit', 5))
        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100."}), 400
    except ValueError:
        return jsonify({"error": "Invalid value for 'limit' parameter."}), 400

    # Call the new function to retrieve data
    history_data = get_history_from_db(limit)
    
    # Check for errors returned by the database function
    if isinstance(history_data, str) and history_data.startswith("Database Error:"):
        return jsonify({"status": "error", "message": history_data}), 500

    # Return the successfully fetched list of records
    return jsonify({
        "status": "ok",
        "count": len(history_data),
        "records": history_data
    })


if __name__ == "__main__":
    init_db() 
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
