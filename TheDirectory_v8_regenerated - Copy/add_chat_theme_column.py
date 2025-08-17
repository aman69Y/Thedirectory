import sqlite3
import os

# Connect to the database
db_path = os.path.join('instance', 'the_directory.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add the chat_theme column to the user table
try:
    cursor.execute("ALTER TABLE user ADD COLUMN chat_theme VARCHAR(10) DEFAULT 'green'")
    conn.commit()
    print("Successfully added chat_theme column to user table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column chat_theme already exists")
    else:
        print(f"Error adding column: {e}")

# Verify the schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
schema = cursor.fetchone()
if schema:
    print("\nUpdated user table schema:")
    print(schema[0])

conn.close()
