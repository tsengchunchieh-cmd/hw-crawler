# ... (Existing imports: requests, json, sqlite3, datetime, etc.)

# --- Configuration (Unchanged) ---
DATABASE_NAME = "weather_data.db"
# ... (Other functions: init_db, get_weather_data, save_to_db remain the same)

# --- New Function: Retrieval Logic ---

def get_history_from_db(limit: int = 10) -> Union[list[Dict[str, Any]], str]:
    """
    Retrieves the most recent weather records from the SQLite database.

    :param limit: The maximum number of records to retrieve.
    :return: A list of dictionaries representing the records, or an error string.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        # Use row_factory to get results as dictionaries (rows) instead of tuples
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # SQL SELECT statement: retrieve the newest records first
        cursor.execute("""
            SELECT id, dataset_id, fetch_timestamp, location_count, raw_data 
            FROM weather_records 
            ORDER BY fetch_timestamp DESC 
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Convert sqlite3.Row objects to standard Python dictionaries
        history_list = [dict(row) for row in rows]
        
        # Optional: Parse the raw_data JSON string back into a dictionary
        # In a real app, you might want to return only partial data to save bandwidth
        for record in history_list:
            try:
                # Replace the raw_data string with the parsed JSON object
                record['raw_data'] = json.loads(record['raw_data'])
            except json.JSONDecodeError:
                # Handle cases where the stored JSON might be corrupted
                record['raw_data'] = {"error": "Corrupted JSON data in DB"}

        return history_list

    except sqlite3.Error as e:
        return f"Database Error: Failed to retrieve history from SQLite: {e}"
