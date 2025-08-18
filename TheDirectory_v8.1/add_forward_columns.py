import sqlite3

def add_forward_columns():
    conn = sqlite3.connect('instance/the_directory.db')
    cursor = conn.cursor()

    try:
        cursor.execute('ALTER TABLE message ADD COLUMN is_forwarded BOOLEAN DEFAULT FALSE')
        print("Column 'is_forwarded' added successfully.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Column 'is_forwarded' already exists.")
        else:
            raise

    try:
        cursor.execute('ALTER TABLE message ADD COLUMN forwarded_from_id INTEGER REFERENCES user(id)')
        print("Column 'forwarded_from_id' added successfully.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Column 'forwarded_from_id' already exists.")
        else:
            raise

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_forward_columns()
