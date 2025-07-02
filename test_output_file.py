import os
import csv
from pathlib import Path

def test_output_file_name():
    """Test that the output file is named 'frame_times.txt'."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Check if frame_times.txt exists in the script directory
    output_file = script_dir / "frame_times.txt"
    
    if output_file.exists():
        print(f"PASS: Output file '{output_file}' exists.")
        
        # Check if the file is in comma-separated format
        with open(output_file, 'r') as f:
            # Try to read the file as CSV
            try:
                reader = csv.reader(f)
                header = next(reader)  # Read the header row
                first_row = next(reader, None)  # Read the first data row if it exists
                
                if header and len(header) >= 2 and header[0] == "Frame" and header[1] == "Timestamp":
                    print(f"PASS: Output file has the correct header: {header}")
                else:
                    print(f"FAIL: Output file has incorrect header: {header}")
                
                if first_row and len(first_row) >= 2:
                    print(f"PASS: Output file has data in comma-separated format: {first_row}")
                else:
                    print(f"FAIL: Output file does not have data in the expected format.")
            except Exception as e:
                print(f"FAIL: Error reading output file as CSV: {e}")
    else:
        print(f"FAIL: Output file '{output_file}' does not exist.")
        
        # Check if any *_timestamps.csv files exist (old format)
        old_format_files = list(script_dir.glob("*_timestamps.csv"))
        if old_format_files:
            print(f"FAIL: Found files in the old format: {old_format_files}")
        else:
            print("INFO: No files in the old format found.")

if __name__ == "__main__":
    test_output_file_name()