import sqlite3
import os

DB_FILE = "vostokstat.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        print("Attempting to add 'side' column to 'squads' table...")
        cursor.execute("ALTER TABLE squads ADD COLUMN side VARCHAR")
        conn.commit()
        print("Successfully added 'side' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("Column 'side' already exists. Skipping.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
