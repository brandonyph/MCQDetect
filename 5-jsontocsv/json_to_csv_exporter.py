import json
import csv
import os
import sys
import argparse

def export_answers_to_csv(json_file='my_answers.json', csv_file='answers.csv'):
    """
    Read answers from JSON file and export to CSV.
    If CSV exists, add a new row. If not, create new CSV with headers.
    """
    
    # Read the JSON file
    try:
        with open(json_file, 'r') as f:
            answers_dict = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
        return
    
    # Create ordered list of answers from 1 to 50
    ordered_answers = []
    for i in range(1, 51):
        answer = answers_dict.get(str(i), 'NA')  # Use 'NA' if question not found
        ordered_answers.append(answer)
    
    # Check if CSV file exists
    file_exists = os.path.exists(csv_file)
    
    # Write to CSV
    try:
        with open(csv_file, 'a', newline='') as f:  # 'a' for append mode
            writer = csv.writer(f)
            
            # If file doesn't exist or is empty, write headers
            if not file_exists or os.path.getsize(csv_file) == 0:
                headers = [f'Q{i}' for i in range(1, 51)]
                writer.writerow(headers)
                print(f"Created new CSV file: {csv_file}")
            else:
                print(f"Adding new row to existing CSV: {csv_file}")
            
            # Write the answers row
            writer.writerow(ordered_answers)
            print("Answers exported successfully!")
            
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return
    
    # Display summary
    print(f"\nSummary:")
    print(f"- Total questions processed: 50")
    print(f"- Questions with answers: {len([a for a in ordered_answers if a != 'NA'])}")
    print(f"- Questions without answers: {len([a for a in ordered_answers if a == 'NA'])}")
    
    # Show missing questions if any
    missing_questions = [i for i in range(1, 51) if str(i) not in answers_dict]
    if missing_questions:
        print(f"- Missing question numbers: {missing_questions}")

def main():
    # Method 1: Command line arguments with argparse
    parser = argparse.ArgumentParser(description='Export JSON answers to CSV')
    parser.add_argument('-i', '--input', default='my_answers.json', 
                       help='Input JSON file (default: my_answers.json)')
    parser.add_argument('-o', '--output', default='answers.csv',
                       help='Output CSV file (default: answers.csv)')
    
    args = parser.parse_args()
    
    # Method 2: Interactive input if no arguments provided
    if len(sys.argv) == 1:  # No command line arguments
        json_file = input("Enter JSON input file name (press Enter for 'my_answers.json'): ").strip()
        if not json_file:
            json_file = 'my_answers.json'
            
        csv_file = input("Enter CSV output file name (press Enter for 'answers.csv'): ").strip()
        if not csv_file:
            csv_file = 'answers.csv'
    else:
        json_file = args.input
        csv_file = args.output
    
    print(f"Input file: {json_file}")
    print(f"Output file: {csv_file}")
    print("-" * 40)
    
    # Run the export function
    export_answers_to_csv(json_file, csv_file)
    
    # Optional: Display the CSV content for verification
    try:
        print(f"\nCurrent CSV content from {csv_file}:")
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    print("Headers:", row[:10], "... (showing first 10)")
                else:
                    print(f"Row {i}:", row[:10], "... (showing first 10)")
    except FileNotFoundError:
        print("CSV file not found for display.")

if __name__ == "__main__":
    main()