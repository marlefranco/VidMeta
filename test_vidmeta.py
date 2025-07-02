import sys
from pathlib import Path

# Test the Path.with_suffix method
file_path = "C:\\test\\example.avi"
file_path_obj = Path(file_path)

# This is the correct way to use with_suffix
correct_suffix = file_path_obj.with_suffix(".csv")
print(f"Correct suffix: {correct_suffix}")

# This would cause an error
try:
    incorrect_suffix = file_path_obj.with_suffix("_timestamps.csv")
    print(f"Incorrect suffix: {incorrect_suffix}")
except ValueError as e:
    print(f"Error: {e}")

# This is the fixed implementation from the updated code
fixed_output_path = file_path_obj.parent / f"{file_path_obj.stem}_timestamps.csv"
print(f"Fixed output path: {fixed_output_path}")

print("Test completed successfully")