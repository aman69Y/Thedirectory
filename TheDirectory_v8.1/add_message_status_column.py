import sqlite3
import os

db_path = os.path.join('instance', 'the_directory.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE message ADD COLUMN status VARCHAR(20) DEFAULT 'sent' NOT NULL")
    conn.commit()
    print("Successfully added status column to message table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column status already exists in message table")
    else:
        print(f"Error adding column: {e}")

conn.close()
