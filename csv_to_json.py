import csv
import json
import os

# Path to your CSV file
csv_file_path = 'Puzzle_Archive_JSONs.csv'
output_dir = 'puzzles'  # The directory where JSON files will be saved

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Function to convert CSV to individual JSON files
def convert_csv_to_json():
    with open(csv_file_path, mode='r') as csv_file:
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=1):
            # Create a filename for each JSON
            filename = f"{i:03}.json"  # Format to ensure 3-digit numbers (001.json, 002.json, etc.)
            file_path = os.path.join(output_dir, filename)

            # Convert row data to JSON and write to file
            with open(file_path, mode='w') as json_file:
                json.dump(row, json_file, indent=4)

            print(f"Saved: {file_path}")

# Ensure the function runs only if this file is the main script
if __name__ == "__main__":
    convert_csv_to_json()
