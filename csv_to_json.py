import csv
import json
import os

csv_file_path = 'Puzzle_Archive_JSONs.csv'
output_dir = 'puzzles'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def convert_csv_to_json():
    with open(csv_file_path, mode='r') as csv_file:
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=1):
            filename = f"{i:03}.json"
            file_path = os.path.join(output_dir, filename)

            # ✅ Only keep the 'Phrase' column and lowercase the key
            phrase_value = row.get("Phrase", "").strip()

            cleaned_data = {
                "phrase": phrase_value  # lowercase key for compatibility with your game
            }

            with open(file_path, mode='w') as json_file:
                json.dump(cleaned_data, json_file, indent=4)

            print(f"Saved: {file_path}")

if __name__ == "__main__":
    convert_csv_to_json()
