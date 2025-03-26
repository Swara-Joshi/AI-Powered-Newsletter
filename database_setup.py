import sqlite3

# Connect to the database (creates if not exists)
conn = sqlite3.connect("newsletter.db")
cursor = conn.cursor()

# Create subscribers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    preference TEXT NOT NULL
);
""")

conn.commit()
conn.close()

print("Database and table created successfully!")
