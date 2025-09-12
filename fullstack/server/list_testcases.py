import json
import sys

def extract_and_sort_testcase_names(json_file_path, output_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        testcase_names = []
        if "testcases" in data and isinstance(data["testcases"], list):
            for testcase in data["testcases"]:
                if "prompt" in testcase and "name" in testcase["prompt"]:
                    testcase_names.append(testcase["prompt"]["name"])

        testcase_names.sort()

        with open(output_file_path, 'w', encoding='utf-8') as f:
            for name in testcase_names:
                f.write(name + '\n')

        print(f"Successfully extracted and saved {len(testcase_names)} test case names to {output_file_path}")

    except FileNotFoundError:
        print(f"Error: The file '{json_file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file '{json_file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python list_names.py <path_to_json_file>")
        sys.exit(1)

    input_json_file = sys.argv[1]
    output_txt_file = "tc_name.txt"
    extract_and_sort_testcase_names(input_json_file, output_txt_file)