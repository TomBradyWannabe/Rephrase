import re

MAX_LETTERS = 21

with open("puzzles.txt") as f:
    phrases = [line.strip() for line in f if line.strip()]

def letter_count(phrase):
    return len(re.sub(r'[^A-Za-z]', '', phrase))

filtered = [p for p in phrases if letter_count(p) <= MAX_LETTERS]

with open("puzzles.txt", "w") as f:
    for phrase in filtered:
        f.write(phrase + "\n")

print(f"✅ Overwrote puzzles.txt with {len(filtered)} phrases out of {len(phrases)} total.")
