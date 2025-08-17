import sqlite3
import os

# Connect to the database
db_path = os.path.join('instance', 'the_directory.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add the message_theme column to the user table
try:
    cursor.execute("ALTER TABLE user ADD COLUMN message_theme VARCHAR(10) DEFAULT 'green'")
    conn.commit()
    print("Successfully added message_theme column to user table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("message_theme column already exists")
    else:
        print(f"Error: {e}")

conn.close()
