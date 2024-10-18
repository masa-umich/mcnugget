import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('metadata.db')

# Create a cursor object
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Query a specific table (replace 'your_table_name' with an actual table name)
cursor.execute("SELECT * FROM synnax LIMIT 1000;")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()
