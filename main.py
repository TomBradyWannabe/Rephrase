from flask import Flask, request, render_template, jsonify, send_from_directory
from collections import Counter
from datetime import datetime, date
import hashlib
import pytz
import random
import os
import json

app = Flask(__name__)

MIN_WORD_LEN = 3
PUZZLE_START_DATE = date(2025, 7, 10)

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
    word = request.json.get('word', '').lower()
    phrase = get_daily_phrase()
    phrase_letters = Counter(c for c in phrase.lower() if c.isalpha())
    phrase_words = set(phrase.lower().split())

    if len(word) < MIN_WORD_LEN:
        return jsonify({'ok': False, 'message': 'Minimum three letters required.'})

    if word not in VALID_WORDS:
        return jsonify({'ok': False, 'message': 'Not a valid word.'})

    if word in phrase_words:
        return jsonify({'ok': False, 'message': 'That word is part of the original phrase.'})

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
    phrase = get_daily_phrase()
    phrase_letters = Counter(c for c in phrase.lower() if c.isalpha())
    used = Counter()
    words = request.json.get('words', [])

    for w in words:
        used += Counter(w.lower())

    for l, cnt in used.items():
        if cnt > phrase_letters.get(l, 0):
            return jsonify({'ok': False, 'message': f"Letter '{l}' overused."})

    total_letters = sum(phrase_letters.values())
    used_letters = sum(min(cnt, phrase_letters[l]) for l, cnt in used.items())
    percent = int(used_letters / total_letters * 100)

    if request.json.get("gave_up"):
        return jsonify({
            'ok': True,
            'gave_up': True,
            'message': random.choice(GIVE_UP_MESSAGES),
            'percent': percent,
            'used_letters': used_letters,
            'total_letters': total_letters
        })

    return jsonify({
        'ok': True,
        'percent': percent,
        'used_letters': used_letters,
        'total_letters': total_letters
    })

@app.route('/day/<int:day>')
def play_archive_day(day):
    try:
        with open(f'puzzles/{day:03}.json') as f:
            data = json.load(f)
        phrase = data['phrase'].upper()
    except FileNotFoundError:
        return "Puzzle not found", 404

    return render_template(
        'index.html',
        phrase=phrase,
        date=f"Archive Day {day}",
        puzzle_number=day,
        archive=True
    )

@app.route('/archive')
def archive():
    # Get the list of all JSON files in the puzzles folder
    puzzle_files = [f for f in os.listdir('puzzles') if f.endswith('.json')]
    past_days = [int(f.split('.')[0]) for f in puzzle_files]  # Extract the day number from the filename
    past_days.sort()  # Sort the days if they aren't already sorted

    # Get the current day number (e.g., if today is Day 2, then exclude it)
    current_day = get_puzzle_number()

    # Exclude the current day from the past_days list
    past_days = [day for day in past_days if day < current_day]

    return render_template('archive.html', past_days=past_days)

@app.route('/archive/<int:day>')
def get_archive(day):
    try:
        # Zero-pad the day number to match the file naming convention like 001.json
        filename = f"puzzles/{day:03}.json"  # Ensure 'puzzles' folder is in the correct location

        # Print the full path for debugging
        print(f"Attempting to send file: {filename}")

        # Send the file from the 'puzzles' directory
        return send_from_directory('puzzles', filename)

    except FileNotFoundError:
        print(f"File {filename} not found!")
        return jsonify({'error': 'Puzzle not found'}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)  # Ensure Replit runs it on the right port
