import sqlite3
import os

# Connect to the database
db_path = os.path.join('instance', 'the_directory.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the schema for the user table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
schema = cursor.fetchone()
if schema:
    print("User table schema:")
    print(schema[0])
else:
    print("User table not found")

conn.close()
