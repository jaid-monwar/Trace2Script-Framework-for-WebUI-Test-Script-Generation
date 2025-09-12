
import hashlib
import json
import os
import sys
from typing import Any, Dict


def calculate_screenshot_hash(screenshot_data: str) -> str:
    return hashlib.sha256(screenshot_data.encode()).hexdigest()

def process_json_file(file_path: str) -> None:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    print(f"Loading JSON file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    screenshot_hash_to_number = {}
    next_sequence_number = 1
    
    processed_count = 0
    total_screenshots = 0
    
    if 'history' in data and isinstance(data['history'], list):
        for entry in data['history']:
            if isinstance(entry, dict) and 'state' in entry:
                if isinstance(entry['state'], dict) and 'screenshot' in entry['state']:
                    if entry['state']['screenshot']:
                        total_screenshots += 1
    
    print(f"Found {total_screenshots} screenshots to process")
    
    if 'history' in data and isinstance(data['history'], list):
        for entry_idx, entry in enumerate(data['history']):
            if isinstance(entry, dict) and 'state' in entry:
                if isinstance(entry['state'], dict) and 'screenshot' in entry['state']:
                    screenshot_data = entry['state']['screenshot']
                    
                    if screenshot_data:
                        processed_count += 1
                        
                        screenshot_hash = calculate_screenshot_hash(str(screenshot_data))
                        
                        if screenshot_hash in screenshot_hash_to_number:
                            sequence_number = screenshot_hash_to_number[screenshot_hash]
                            print(f"  [{processed_count}/{total_screenshots}] Entry {entry_idx}: Duplicate screenshot, using number {sequence_number}")
                        else:
                            sequence_number = next_sequence_number
                            screenshot_hash_to_number[screenshot_hash] = sequence_number
                            next_sequence_number += 1
                            print(f"  [{processed_count}/{total_screenshots}] Entry {entry_idx}: New screenshot, assigned number {sequence_number}")
                        
                        entry['state']['screenshot'] = sequence_number
    
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(file_name)
    output_path = os.path.join(file_dir, f"{name_without_ext}_processed{ext}")
    
    print(f"Saving processed JSON file: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)
    
    unique_screenshots = len(screenshot_hash_to_number)
    print(f"\nProcessing complete!")
    print(f"  Original file: {file_path}")
    print(f"  New processed file: {output_path}")
    print(f"  Total screenshots processed: {processed_count}")
    print(f"  Unique screenshots found: {unique_screenshots}")
    print(f"  Duplicate screenshots: {processed_count - unique_screenshots}")
    print(f"  Sequential numbers assigned: 1 to {unique_screenshots}")

def main():
    default_path = "tmp/agent_history/mit_ocw/website_accessebility_info/website_accessebility_info.json"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path
    
    print("=== Agent History JSON Screenshot Processor ===")
    print("This script replaces screenshot data with sequential numbers")
    print("Identical screenshots will receive the same sequence number")
    print("Creates a new output file instead of modifying the original")
    print("=" * 50)
    
    process_json_file(file_path)

if __name__ == "__main__":
    main()