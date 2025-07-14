import json
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

# Load your big word list (already in your project)
with open("wordlist.txt") as f:
    VALID_WORDS = {
        w.strip().lower()
        for w in f
        if w.strip().isalpha() and len(w.strip()) >= 3
    }

def is_valid(word, available_letters):
    """Check if word is in dictionary and can be made from given letters."""
    return word in VALID_WORDS and not (Counter(word) - available_letters)

def solve_phrase(phrase):
    """Try to find a full anagram of the phrase using valid words."""
    letters = Counter(c for c in phrase.lower() if c.isalpha())
    solutions = []

    def backtrack(path, remaining):
        if sum(remaining.values()) == 0:
            solutions.append(path[:])
            return True  # stop after first full solution

        for word in VALID_WORDS:
            if len(word) > sum(remaining.values()):
                continue
            wc = Counter(word)
            if not wc - remaining:
                path.append(word)
                if backtrack(path, remaining - wc):
                    return True
                path.pop()
        return False

    found = backtrack([], letters)
    return solutions[0] if found else None

# Read your 500 phrases (from the file created earlier)
with open("phrases.txt") as f:
    phrases = [line.strip() for line in f if line.strip()]

results = []
start_time = time.time()

for phrase in phrases:
    t0 = time.time()
    solution = solve_phrase(phrase)
    if solution:
        results.append({
            "phrase": phrase,
            "solution": solution,
            "word_count": len(solution),
            "letter_count": sum(len(w) for w in solution),
            "time": round(time.time() - t0, 2)
        })

# Save good ones to a file
with open("solvable_puzzles.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Done! Found {len(results)} solvable puzzles out of {len(phrases)} in {round(time.time() - start_time, 2)}s.")
