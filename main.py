from flask import Flask, request, render_template, jsonify, send_from_directory
from collections import Counter
from datetime import datetime, date, timedelta
import hashlib
import pytz
import random
import os
import json
import psycopg2
import dotenv
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def get_pg_connection():
    return psycopg2.connect(DB_URL)


app = Flask(__name__)

MIN_WORD_LEN = 3
PUZZLE_START_DATE = date(2025, 7, 23)

# Load valid words once at startup
with open('wordlist.txt') as f:
    VALID_WORDS = {
        w.strip().lower()
        for w in f
        if w.strip().isalpha() and len(w.strip()) >= MIN_WORD_LEN
    }

# Load all phrases once at startup
def load_puzzles():
    with open("puzzles.txt") as f:
        return [line.strip() for line in f if line.strip()]

# Give-up message pool
GIVE_UP_MESSAGES = [
    "You gave it your best shot! There’s always tomorrow’s phrase.",
    "No shame in walking away — those last few letters were sneaky.",
    "You bowed out gracefully. Puzzle complete-ish!",
    "The phrase wins this round! But you'll get the next one.",
    "You waved the white flag 🏳️ … still a valiant effort!",
    "Puzzle: 1, You: still awesome.",
    "You surrendered — but we respect your strategic retreat.",
    "You’ve left a few letters on the table. A poetic mystery remains!",
    "Game over… or should we say: *Game, mostly solved?*",
    "Not quite a mic drop, but still a solid run."
]

def get_today():
    tz = pytz.timezone("America/Los_Angeles")
    return datetime.now(tz).date()

def get_today_date_string():
    return get_today().strftime("%A, %B %d, %Y")

def get_puzzle_number():
    return (get_today() - PUZZLE_START_DATE).days + 1  # Puzzle number based on date

def get_daily_phrase():
    puzzle_number = get_puzzle_number()
    puzzles = load_puzzles()  # Load puzzles from file
    if puzzle_number <= len(puzzles):  # Ensure we're within the range of available puzzles
        return puzzles[puzzle_number - 1]  # Adjust for 0-based index
    else:
        return "No more puzzles available"
        
@app.route('/leaderboard_submit', methods=['POST'])
def leaderboard_submit():
    print("📥 Submission attempt received!")
    data = request.get_json()
    print("🔎 Received leaderboard submission:", data)
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        longest_word = max(data.get('submitted_words', []), key=len, default="")

        cursor.execute("""
            INSERT INTO leaderboard (
                puzzle_number,
                puzzle_date,
                name,
                time_seconds,
                percent_complete,
                word_count,
                five_plus_words,
                seven_plus_words,
                longest_word
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['puzzle_number'],
            data['puzzle_date'],
            data['name'],
            data['time_seconds'],         
            data['percent_complete'],     
            data['word_count'],           
            data['five_plus_words'],  
            data['seven_plus_words'],
            longest_word
        ))

        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    except Exception as e:
        print("Leaderboard insert error:", e)
        return jsonify({'ok': False, 'error': str(e)})


@app.route('/leaderboard/<int:puzzle_number>')
def get_leaderboard(puzzle_number):
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, time_seconds, percent_complete, word_count, five_plus_words, seven_plus_words, longest_word
            FROM leaderboard
            WHERE puzzle_number = %s
            ORDER BY 
            CASE WHEN percent_complete = 100 THEN 0 ELSE 1 END,
            CASE WHEN percent_complete = 100 THEN time_seconds ELSE NULL END ASC,
            CASE WHEN percent_complete < 100 THEN percent_complete ELSE NULL END DESC
            LIMIT 10
        """, (puzzle_number,))
        rows = cursor.fetchall()
        conn.close()

        leaderboard = [
            {
                "name": row[0],
                "time_seconds": row[1],
                "percent": row[2],
                "words": row[3],
                "five_plus": row[4],
                "seven_plus": row[5],
                "longest": row[6],
            }
            for row in rows
        ]
        return jsonify({"ok": True, "leaderboard": leaderboard})
    except Exception as e:
        print("Error fetching leaderboard:", e)
        return jsonify({"ok": False, "error": str(e)})

@app.route('/')
def index():
    phrase = get_daily_phrase()
    return render_template(
        'index.html',
        phrase=phrase,
        date=get_today_date_string(),
        puzzle_number=get_puzzle_number(),
        archive=False
    )
    

@app.route('/submit', methods=['POST'])
def submit_word():
    if not request.json:
        return jsonify({'ok': False, 'message': 'Invalid request format.'})
    
    word = request.json.get('word', '').lower()

    # ✅ NEW: Get puzzle number from request, if it's an archive puzzle
    puzzle_number = request.json.get('puzzle_number')
    if puzzle_number:
        try:
            with open(f'puzzles/{int(puzzle_number):03}.json') as f:
                data = json.load(f)
            phrase = data['phrase']
        except Exception:
            return jsonify({'ok': False, 'message': 'Could not load archive puzzle.'})
    else:
        phrase = get_daily_phrase()

    # ✅ Existing validation logic
    phrase_letters = Counter(c for c in phrase.lower() if c.isalpha())
    phrase_words = set(phrase.lower().split())

    if len(word) < MIN_WORD_LEN:
        return jsonify({'ok': False, 'message': 'Minimum three letters required.'})

    if word not in VALID_WORDS:
        return jsonify({'ok': False, 'message': 'Not a valid word.'})

    if word in phrase_words:
        return jsonify({'ok': False, 'message': 'That word is part of the original phrase.'})

    if word.endswith('s'):
        base_word = word[:-1]
        if base_word in phrase_words:
            return jsonify({'ok': False, 'message': f'"{word}" is invalid because it is just "{base_word}" from the phrase with an added "s".'})

    for phrase_word in phrase_words:
        if phrase_word.startswith(word) or phrase_word.endswith(word):
            if word != phrase_word and len(word) >= 3:
                return jsonify({'ok': False, 'message': 'That word is part of a word from the original phrase.'})

    word_letter_counts = Counter(word)
    for letter, count in word_letter_counts.items():
        if count > phrase_letters.get(letter, 0):
            return jsonify({'ok': False, 'message': f"Letter '{letter}' not in phrase or overused."})

    return jsonify({'ok': True})


@app.route('/progress', methods=['POST'])
def progress():
    if not request.json:
        return jsonify({'ok': False, 'message': 'Invalid request format.'})
    
    words = request.json.get('words', [])
    gave_up = request.json.get("gave_up", False)

    # ✅ Use puzzle_number if provided (archive), otherwise use today's
    puzzle_number = request.json.get('puzzle_number')
    if puzzle_number:
        try:
            with open(f'puzzles/{int(puzzle_number):03}.json') as f:
                data = json.load(f)
            phrase = data['phrase']
        except Exception:
            return jsonify({'ok': False, 'message': 'Could not load archive puzzle.'})
    else:
        phrase = get_daily_phrase()

    phrase_letters = Counter(c for c in phrase.lower() if c.isalpha())
    used = Counter()

    for w in words:
        used += Counter(w.lower())

    for l, cnt in used.items():
        if cnt > phrase_letters.get(l, 0):
            return jsonify({'ok': False, 'message': f"Letter '{l.upper()}' overused."})

    total_letters = sum(phrase_letters.values())
    used_letters = sum(min(cnt, phrase_letters[l]) for l, cnt in used.items())
    percent = int(used_letters / total_letters * 100)

    return jsonify({
        'ok': True,
        'gave_up': gave_up,
        'percent': percent,
        'used_letters': used_letters,
        'total_letters': total_letters,
        'message': random.choice(GIVE_UP_MESSAGES) if gave_up else ""
    })


@app.route('/day/<int:day>')
def play_archive_day(day):
    try:
        with open(f'puzzles/{day:03}.json') as f:
            data = json.load(f)
        phrase = data['phrase'].upper()

        # ✅ Define the correct archive date
        archive_date = PUZZLE_START_DATE + timedelta(days=day - 1)

    except FileNotFoundError:
        return "Puzzle not found", 404

    return render_template(
        'index.html',
        phrase=phrase,
        date=archive_date.strftime("%B %d, %Y"),
        puzzle_number=day,
        archive=True
    )


@app.route('/archive')
def archive():
    # Get the list of all JSON files in the puzzles folder
    puzzle_files = [f for f in os.listdir('puzzles') if f.endswith('.json')]
    past_days = [int(f.split('.')[0]) for f in puzzle_files]
    past_days.sort()

    current_day = get_puzzle_number()
    past_days = [day for day in past_days if day < current_day]

    # 🆕 Build a list of {day, date_str} for display
    puzzle_dates = []
    for day in past_days:
        archive_date = PUZZLE_START_DATE + timedelta(days=day - 1)
        puzzle_dates.append({
            "day": day,
            "date_str": archive_date.strftime("%B %d, %Y")  # e.g. "July 14, 2025"
        })

    return render_template('archive.html', puzzle_dates=puzzle_dates)

@app.route('/archive/<int:day>')
def get_archive(day):
    # Zero-pad the day number to match the file naming convention like 001.json
    filename = f"puzzles/{day:03}.json"  # Ensure 'puzzles' folder is in the correct location
    
    try:
        # Print the full path for debugging
        print(f"Attempting to send file: {filename}")

        # Send the file from the 'puzzles' directory
        return send_from_directory('puzzles', filename)

    except FileNotFoundError:
        print(f"File {filename} not found!")
        return jsonify({'error': 'Puzzle not found'}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Ensure Replit runs it on the right port
    
@app.route('/test_submit')
def test_submit():
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leaderboard (
                puzzle_number,
                puzzle_date,
                name,
                time_seconds,
                percent_complete,
                word_count,
                five_plus_words,
                seven_plus_words,
                longest_word
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            999,  # test puzzle number
            "2025-07-23",
            "Tester",
            123,
            100,
            17,
            5,
            2,
            "excellent"
        ))
        conn.commit()
        conn.close()
        return "✅ Test submission complete"
    except Exception as e:
        return f"❌ Test submission failed: {e}"
        
@app.route('/test_fetch')
def test_fetch():
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, time_seconds, percent_complete, longest_word
            FROM leaderboard
            WHERE puzzle_number = %s
        """, (999,))
        rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return f"❌ Fetch failed: {e}"
