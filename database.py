import datetime
import json
import sqlite3


conn = sqlite3.connect("cache.db", check_same_thread=False)


def init_db():
    """This function creates the tables in the database"""

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp TEXT
            ) """)
        

def save_cache(key, data):
    """This function saves the data in the database"""

    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO cache (key, data, timestamp)
            VALUES (?, ?, datetime('now'))
        """, (key, json.dumps(data)))


def get_cache(key):
    """This function retrieves the data from the database"""

    with conn:
        cursor = conn.execute("""
            SELECT data, timestamp FROM cache WHERE key = ?
        """, (key,))
        row = cursor.fetchone()

        if row:
            return json.loads(row[0])
        else:
            return None
        

def is_valid_cache(key, hours):
    """This function checks if the cache is valid based on time"""

    with conn:
        # Retrieve the timestamp of the cache entry using the provided key
        cursor = conn.execute("""
            SELECT timestamp FROM cache WHERE key = ?
        """, (key,))
        row = cursor.fetchone()

        # If no entry exists in the database, the cache is invalid
        if row is None:
            return False

        # Convert the stored timestamp (string) to a datetime object
        saved_time = datetime.datetime.fromisoformat(row[0])
        # Get the current date and time
        now = datetime.datetime.now()
        # Calculate the time difference between now and when it was saved
        difference = now - saved_time
        # Define the maximum time limit that the cache can have (in hours)
        limit = datetime.timedelta(hours=hours)

        # Return True if the cache is still "fresh" (more recent than the limit)
        return difference < limit