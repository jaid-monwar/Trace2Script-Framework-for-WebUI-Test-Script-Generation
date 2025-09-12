
import os
import sys
from pathlib import Path


def list_directories(target_path):
    try:
        path = Path(target_path)
        
        if not path.exists():
            print(f"Error: Path '{target_path}' does not exist.")
            return []
        
        if not path.is_dir():
            print(f"Error: '{target_path}' is not a directory.")
            return []
        
        directories = [item.name for item in path.iterdir() if item.is_dir()]
        
        directories.sort()
        
        return directories
        
    except PermissionError:
        print(f"Error: Permission denied to access '{target_path}'.")
        return []
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def save_to_file(directories, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for directory in directories:
                f.write(directory + '\n')
        
        print(f"Successfully saved {len(directories)} directory names to '{output_file}'")
        
    except Exception as e:
        print(f"Error writing to file '{output_file}': {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python list_directories.py <path>")
        print("Example: python list_directories.py dataset/openai_gpt-4o/mdn")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    output_filename = "tc_name.txt"
    
    print(f"Scanning directory: {target_path}")
    
    directories = list_directories(target_path)
    
    if directories:
        print(f"Found {len(directories)} directories:")
        for i, directory in enumerate(directories, 1):
            print(f"  {i}. {directory}")
        
        save_to_file(directories, output_filename)
    else:
        print("No directories found or an error occurred.")

if __name__ == "__main__":
    main()