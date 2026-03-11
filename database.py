import datetime
import json
import sqlite3


conn = sqlite3.connect("cache.db")


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
    """This function checks if the cache is valid"""

    with conn:
        cursor = conn.execute("""
            SELECT timestamp FROM cache WHERE key = ?
        """, (key,))
        row = cursor.fetchone()

        if row is None:
            return False

        saved_time = datetime.datetime.fromisoformat(row[0])
        now = datetime.datetime.now()
        difference = now - saved_time
        limit = datetime.timedelta(hours=hours)

        return difference < limit