import sqlite3

conn = sqlite3.connect('leaderboard.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    puzzle_number INTEGER NOT NULL,
    puzzle_date TEXT NOT NULL,
    name TEXT NOT NULL,
    time_seconds INTEGER NOT NULL,
    percent_complete INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    five_plus_words INTEGER NOT NULL,
    seven_plus_words INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("Leaderboard table created.")
