import sqlite3
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def initialize_database():
    db_path = config.DB_PATH
    print(f"Initializing SQLite database at: {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print("\nDatabase 'smartcart.db' and all 5 tables initialized successfully!")
    except Exception as e:
        print(f"\nError initializing database: {e}")
        raise e

if __name__ == '__main__':
    initialize_database()
