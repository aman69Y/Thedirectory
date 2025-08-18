import sqlite3

def add_reply_to_column():
    conn = sqlite3.connect('instance/the_directory.db')
    cursor = conn.cursor()

    try:
        cursor.execute('PRAGMA table_info(message)')
        columns = [column[1] for column in cursor.fetchall()]
        if 'reply_to_id' not in columns:
            cursor.execute('ALTER TABLE message ADD COLUMN reply_to_id INTEGER REFERENCES message(id)')
            print("Column 'reply_to_id' added to 'message' table.")
        else:
            print("Column 'reply_to_id' already exists in 'message' table.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == '__main__':
    add_reply_to_column()
