

import sqlite3

conn = sqlite3.connect("findings.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT,
    snippet TEXT,
    source_url TEXT
)
""")

conn.commit()
conn.close()

print("Database initialized.")
