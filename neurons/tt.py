import sqlite3
import os

# Define the path to the database file
db_path = "/Users/napoli/bittensor-db/default/validator/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"

# Check if the file exists
if not os.path.isfile(db_path):
    print(f"The file at path {db_path} does not exist.")
else:
    # Connect to the database
    conn = sqlite3.connect(db_path)

    # Create a cursor object
    cursor = conn.cursor()

    # Get the list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Loop through all tables
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")

        # Get the list of all columns in the table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print(f"Columns: {', '.join(column_names)}")

        # Get all rows in the table
        cursor.execute(f"SELECT id FROM {table_name};")
        rows = cursor.fetchall()

        # Loop through all rows
        for row in rows:
            print(row)

    # Close the connection
    conn.close()
