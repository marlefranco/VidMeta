import csv
import subprocess
import json
import datetime
import time
import re
import os
from pathlib import Path

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk
import pytesseract

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_all_metadata(path: str) -> dict:
    """Extract all metadata from video using ffprobe."""
    try:
        # Normalize file path for Windows
        path = os.path.normpath(path)

        # Get format metadata
        format_result = subprocess.run([
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            path,
        ], capture_output=True, text=True, check=True)
        format_data = json.loads(format_result.stdout)

        # Get stream metadata
        stream_result = subprocess.run([
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            path,
        ], capture_output=True, text=True, check=True)
        stream_data = json.loads(stream_result.stdout)

        return {
            "format": format_data.get("format", {}),
            "streams": stream_data.get("streams", [])
        }
    except Exception as e:
        print(f"Error getting metadata: {e}")
        return {}


def parse_datetime(datetime_str: str) -> datetime.datetime | None:
    """Parse datetime string from metadata."""
    if not datetime_str:
        return None

    try:
        # Handle ISO format with Z
        if 'Z' in datetime_str:
            return datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        # Try standard ISO format
        return datetime.datetime.fromisoformat(datetime_str)
    except ValueError:
        try:
            # Try other common formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S"
            ]:
                try:
                    return datetime.datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
    return None


def get_creation_time(path: str) -> datetime.datetime | None:
    """Extract creation time from video metadata using ffprobe."""
    try:
        # Normalize file path for Windows
        path = os.path.normpath(path)

        result = subprocess.run([
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_entries",
            "format_tags=creation_time",
            path,
        ], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        value = data.get("format", {}).get("tags", {}).get("creation_time")
        if value:
            return parse_datetime(value)
    except Exception:
        pass
    return None


def select_reference_time(metadata: dict) -> datetime.datetime | None:
    """Display metadata and let user select a reference time."""
    # Create a new window
    select_window = tk.Toplevel()
    select_window.title("Select Reference Time")
    select_window.geometry("800x600")

    # Create a frame for the metadata display
    frame = tk.Frame(select_window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create a scrollbar
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a text widget to display metadata
    text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    text.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=text.yview)

    # Insert metadata into text widget
    text.insert(tk.END, "VIDEO METADATA:\n\n")

    # Dictionary to store potential datetime values
    datetime_values = {}

    # Format metadata
    text.insert(tk.END, "FORMAT METADATA:\n")
    format_data = metadata.get("format", {})
    for key, value in format_data.items():
        if key == "tags" and isinstance(value, dict):
            text.insert(tk.END, "  TAGS:\n")
            for tag_key, tag_value in value.items():
                text.insert(tk.END, f"    {tag_key}: {tag_value}\n")
                # Check if this might be a datetime
                dt = parse_datetime(tag_value)
                if dt:
                    datetime_values[f"format.tags.{tag_key}"] = dt
        else:
            text.insert(tk.END, f"  {key}: {value}\n")
            # Check if this might be a datetime
            dt = parse_datetime(str(value))
            if dt:
                datetime_values[f"format.{key}"] = dt

    # Stream metadata
    text.insert(tk.END, "\nSTREAM METADATA:\n")
    for i, stream in enumerate(metadata.get("streams", [])):
        text.insert(tk.END, f"  STREAM {i}:\n")
        for key, value in stream.items():
            if key == "tags" and isinstance(value, dict):
                text.insert(tk.END, f"    TAGS:\n")
                for tag_key, tag_value in value.items():
                    text.insert(tk.END, f"      {tag_key}: {tag_value}\n")
                    # Check if this might be a datetime
                    dt = parse_datetime(tag_value)
                    if dt:
                        datetime_values[f"stream{i}.tags.{tag_key}"] = dt
            else:
                text.insert(tk.END, f"    {key}: {value}\n")
                # Check if this might be a datetime
                dt = parse_datetime(str(value))
                if dt:
                    datetime_values[f"stream{i}.{key}"] = dt

    text.config(state=tk.DISABLED)  # Make text read-only

    # If no datetime values found
    if not datetime_values:
        messagebox.showinfo("No Time Values", "No time values found in metadata. Using current time.")
        select_window.destroy()
        return None

    # Create a frame for the selection
    select_frame = tk.Frame(select_window)
    select_frame.pack(fill=tk.X, padx=10, pady=10)

    tk.Label(select_frame, text="Select reference time:").pack(side=tk.LEFT)

    # Create a variable to store the selection
    selected_time = tk.StringVar()

    # Sort datetime values by key for consistent display
    sorted_keys = sorted(datetime_values.keys())
    if sorted_keys:
        selected_time.set(sorted_keys[0])  # Default selection

    # Create dropdown menu
    dropdown = tk.OptionMenu(select_frame, selected_time, *sorted_keys)
    dropdown.pack(side=tk.LEFT, padx=5)

    # Create a label to display the selected datetime
    time_label = tk.Label(select_frame, text="")
    time_label.pack(side=tk.LEFT, padx=5)

    # Function to update the time label
    def update_time_label(*args):
        key = selected_time.get()
        if key in datetime_values:
            time_label.config(text=str(datetime_values[key]))

    # Register callback
    selected_time.trace("w", update_time_label)
    update_time_label()  # Initial update

    # Variable to store the result
    result = [None]

    # Function to handle selection
    def on_select():
        key = selected_time.get()
        if key in datetime_values:
            result[0] = datetime_values[key]
        select_window.destroy()

    # Function to handle cancel
    def on_cancel():
        select_window.destroy()

    # Create buttons
    button_frame = tk.Frame(select_window)
    button_frame.pack(fill=tk.X, padx=10, pady=10)

    tk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
    tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)

    # Wait for the window to be closed
    select_window.wait_window()

    return result[0]


def extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height):
    """
    Extract timestamp from the top right corner of the frame using OCR.

    Args:
        frame: The video frame
        roi_x: X-coordinate of the top-left corner of the ROI
        roi_y: Y-coordinate of the top-left corner of the ROI
        roi_width: Width of the ROI
        roi_height: Height of the ROI

    Returns:
        Tuple of (extracted datetime object, original format string) or (None, None) if no timestamp found
    """
    # Verify Tesseract is properly configured
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        print(f"Using Tesseract version: {tesseract_version}")
    except Exception as e:
        print(f"WARNING: Could not verify Tesseract installation: {e}")
        print(f"Current Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
        print("Please ensure Tesseract is properly installed and the path is correct.")
        # Continue anyway, as the error might be with version checking but OCR might still work
    # Extract the region of interest (ROI)
    roi = frame[roi_y:roi_y+roi_height, roi_x:roi_x+roi_width]

    # Create a debug directory if it doesn't exist
    import os
    debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")
    os.makedirs(debug_dir, exist_ok=True)

    # Save the original ROI for debugging
    original_roi_path = os.path.join(debug_dir, "original_roi.png")
    cv2.imwrite(original_roi_path, roi)
    print(f"Saved original ROI to {original_roi_path}")

    # Convert to grayscale for better OCR results
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Save the grayscale ROI for debugging
    gray_roi_path = os.path.join(debug_dir, "gray_roi.png")
    cv2.imwrite(gray_roi_path, gray)
    print(f"Saved grayscale ROI to {gray_roi_path}")

    # Try different preprocessing methods to handle various text colors and backgrounds
    preprocessing_methods = [
        # Original grayscale
        lambda img: img,
        # Binary threshold (dark text on light background)
        lambda img: cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)[1],
        # Inverse binary threshold (light text on dark background) - optimized for white text
        lambda img: cv2.threshold(img, 120, 255, cv2.THRESH_BINARY_INV)[1],  # Lower threshold for better white text detection
        # Stronger inverse threshold for white text on dark backgrounds
        lambda img: cv2.threshold(img, 80, 255, cv2.THRESH_BINARY_INV)[1],  # Even lower threshold for very faint white text
        # Adaptive threshold
        lambda img: cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
        # Inverse adaptive threshold
        lambda img: cv2.bitwise_not(cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        # Contrast enhancement followed by inverse binary threshold (good for white text)
        lambda img: cv2.threshold(cv2.equalizeHist(img), 120, 255, cv2.THRESH_BINARY_INV)[1],
        # Blur followed by inverse threshold (helps with noisy backgrounds)
        lambda img: cv2.threshold(cv2.GaussianBlur(img, (3, 3), 0), 120, 255, cv2.THRESH_BINARY_INV)[1],
        # Color filtering for white text (new method)
        lambda img: cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)[1],  # High threshold to isolate very white pixels
        # Morphological operations to enhance white text
        lambda img: cv2.morphologyEx(cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)[1], cv2.MORPH_OPEN, np.ones((2,2),np.uint8)),
        # Advanced white text isolation (combines multiple techniques)
        lambda img: cv2.morphologyEx(
            cv2.threshold(
                cv2.GaussianBlur(cv2.equalizeHist(img), (3, 3), 0),  # Equalize and blur to reduce noise
                190, 255, cv2.THRESH_BINARY)[1],  # High threshold for white text
            cv2.MORPH_CLOSE, np.ones((2,2),np.uint8)  # Close small gaps in text
        )
    ]

    # Create a debug directory if it doesn't exist
    import os
    debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")
    os.makedirs(debug_dir, exist_ok=True)

    # Try each preprocessing method until we find a timestamp
    for i, preprocess in enumerate(preprocessing_methods):
        try:
            # Apply preprocessing
            processed_img = preprocess(gray)

            # Save the processed image for debugging
            debug_path = os.path.join(debug_dir, f"preprocess_method_{i}.png")
            cv2.imwrite(debug_path, processed_img)
            print(f"Saved debug image to {debug_path}")

            # Use pytesseract to extract text from the ROI
            try:
                # Restrict characters to improve accuracy and remove newlines
                # Use PSM 7 (treat as single line of text)
                text = pytesseract.image_to_string(
                    processed_img,
                    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789:/.-'
                )
                # Clean up the text
                text = text.replace('\n', ' ').strip()
            except pytesseract.pytesseract.TesseractError as te:
                print(f"Tesseract Error: {te}")
                print("This may indicate an issue with Tesseract installation or configuration.")
                print(f"Current Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
                print("Please ensure Tesseract is properly installed and the path is correct.")
                continue  # Try the next preprocessing method

            # Debug output
            print(f"Method {i} - Extracted text: {text}")

            # Look for various timestamp patterns
            patterns = [
                # Format with 4-digit year: DD/MM/YYYY HH:MM:SS:ZZZ (specific format from issue)
                (r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}:\d{3})', '%d/%m/%Y %H:%M:%S:%f'),
                # Format with 4-digit year: DD/MM/YYYY HH:MM:ss.SSS
                (r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\.\d{3})', '%d/%m/%Y %H:%M:%S.%f'),
                # Standard format: DD/MM/YY HH:MM:ss.SSS
                (r'(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})', '%d/%m/%y %H:%M:%S.%f'),
                # Alternative format with different separators: DD-MM-YY HH:MM:ss.SSS
                (r'(\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})', '%d-%m-%y %H:%M:%S.%f'),
                # Format with no milliseconds: DD/MM/YY HH:MM:ss
                (r'(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})', '%d/%m/%y %H:%M:%S'),
                # US format: MM/DD/YY HH:MM:ss.SSS
                (r'(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})', '%m/%d/%y %H:%M:%S.%f'),
                # Format with different time separator: DD/MM/YY HH-MM-ss.SSS
                (r'(\d{2}/\d{2}/\d{2}\s+\d{2}-\d{2}-\d{2}\.\d{3})', '%d/%m/%y %H-%M-%S.%f'),
                # Format with just time: HH:MM:ss.SSS
                (r'(\d{2}:\d{2}:\d{2}\.\d{3})', '%H:%M:%S.%f')
            ]

            for pattern, fmt in patterns:
                match = re.search(pattern, text)
                if match:
                    timestamp_str = match.group(1)

                    # Handle colon separator in milliseconds
                    if ':' in timestamp_str and fmt.endswith(':%f'):
                        # For the specific format with colon separator for milliseconds,
                        # we need to handle it specially since Python's datetime.strptime
                        # doesn't support colon as a separator for milliseconds

                        # First, check if this is the specific format we're looking for (DD/MM/YYYY HH:MM:SS:ZZZ)
                        if re.match(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}:\d{3}', timestamp_str):
                            # Extract the components manually
                            parts = timestamp_str.split()
                            date_part = parts[0]  # DD/MM/YYYY
                            time_part = parts[1]  # HH:MM:SS:mmm

                            # Split the date and time parts
                            day, month, year = date_part.split('/')

                            # Split the time part and handle the milliseconds
                            time_components = time_part.split(':')
                            hour = time_components[0]
                            minute = time_components[1]
                            second = time_components[2]
                            millisecond = time_components[3]

                            # Create a datetime object manually
                            # The datetime constructor expects (year, month, day, hour, minute, second, microsecond)
                            # Convert milliseconds to microseconds correctly
                            microseconds = int(millisecond)
                            if len(millisecond) == 4:
                                # For 4-digit milliseconds, treat as 0.xxxx seconds
                                microseconds = int(millisecond) * 100
                            elif len(millisecond) > 4:
                                # For longer milliseconds, truncate to 6 digits (microseconds limit)
                                microseconds = int(millisecond[:6])
                            else:
                                # For 1-3 digit milliseconds, multiply by 1000 to convert to microseconds
                                microseconds = int(millisecond) * 1000

                            dt = datetime.datetime(
                                int(year), int(month), int(day),
                                int(hour), int(minute), int(second),
                                microseconds
                            )
                            # Store the original format string
                            original_format = f"{day}/{month}/{year} {hour}:{minute}:{second}:{millisecond}"
                            print(f"Successfully parsed timestamp manually: {dt}")
                            return dt, original_format

                        # If it's not the specific format, fall back to the previous approach
                        # Replace the format string to use dot instead of colon for milliseconds
                        fmt = fmt.replace(':%f', '.%f')
                        # Replace the last colon with a dot in the timestamp string
                        last_colon_index = timestamp_str.rfind(':')
                        if last_colon_index != -1 and len(timestamp_str) - last_colon_index >= 4:
                            # Check if what follows is 3 digits (milliseconds)
                            if timestamp_str[last_colon_index+1:last_colon_index+4].isdigit():
                                timestamp_str = timestamp_str[:last_colon_index] + '.' + timestamp_str[last_colon_index+1:]

                    try:
                        # Parse the timestamp string to a datetime object
                        if fmt == '%H:%M:%S.%f':
                            # For time-only format, use today's date
                            time_obj = datetime.datetime.strptime(timestamp_str, fmt).time()
                            dt = datetime.datetime.combine(datetime.datetime.today().date(), time_obj)
                        else:
                            dt = datetime.datetime.strptime(timestamp_str, fmt)
                        print(f"Successfully parsed timestamp with format {fmt}: {dt}")
                        return dt, timestamp_str
                    except ValueError:
                        print(f"Failed to parse timestamp: {timestamp_str} with format {fmt}")
                        continue
        except Exception as e:
            print(f"OCR error with preprocessing method: {e}")

    # If we've tried all preprocessing methods and still haven't found a timestamp,
    # try one more time with more relaxed patterns
    try:
        # Save a debug image of the final attempt
        debug_path = os.path.join(debug_dir, "final_attempt.png")
        cv2.imwrite(debug_path, gray)
        print(f"Saved final attempt image to {debug_path}")

        # Use the original grayscale image with different PSM modes
        for psm_mode in [7, 6, 3]:  # Try different page segmentation modes
            try:
                text = pytesseract.image_to_string(
                    gray,
                    config=f'--psm {psm_mode} --oem 3 -c tessedit_char_whitelist=0123456789:/.-'
                )
                print(f"Final attempt with PSM {psm_mode} - Extracted text: {text}")

                # Clean up the text
                text = text.replace('\n', ' ').strip()

                # First try to match the exact format we're seeing with PSM 6
                exact_match = re.search(r'(\d{2}/\d{2}/\d{4})(\d{2}):(\d{5}):(\d{3})', text)
                if exact_match:
                    try:
                        # Extract date components
                        date_str = exact_match.group(1)  # DD/MM/YYYY
                        hour = exact_match.group(2)
                        combined_minutes = exact_match.group(3)  # MMHHH - contains both minutes and milliseconds
                        final_milliseconds = exact_match.group(4)

                        # Split the date
                        day, month, year = date_str.split('/')

                        # Extract minutes and milliseconds from combined value
                        minutes = combined_minutes[:2]  # First two digits are minutes
                        seconds = combined_minutes[2:4]  # Next two digits are seconds
                        milliseconds = combined_minutes[4:] + final_milliseconds  # Combine all milliseconds

                        print(f"Parsed components - Date: {year}-{month}-{day}, Time: {hour}:{minutes}:{seconds}.{milliseconds}")

                        # Create datetime object manually
                        # Convert milliseconds to microseconds correctly
                        # If milliseconds has 4 digits (e.g., 3287), it represents 0.3287 seconds
                        # So we need to convert it to 328700 microseconds
                        microseconds = int(milliseconds)
                        if len(milliseconds) == 4:
                            # For 4-digit milliseconds, treat as 0.xxxx seconds
                            microseconds = int(milliseconds) * 100
                        elif len(milliseconds) > 4:
                            # For longer milliseconds, truncate to 6 digits (microseconds limit)
                            microseconds = int(milliseconds[:6])
                        else:
                            # For 1-3 digit milliseconds, multiply by 1000 to convert to microseconds
                            microseconds = int(milliseconds) * 1000

                        dt = datetime.datetime(
                            int(year), int(month), int(day),
                            int(hour), int(minutes), int(seconds),
                            microseconds
                        )
                        # Store the original format string
                        original_format = f"{day}/{month}/{year} {hour}:{minutes}:{seconds}.{milliseconds}"
                        print(f"Successfully parsed timestamp manually: {dt}")
                        return dt, original_format
                    except (ValueError, IndexError) as e:
                        print(f"Failed to parse exact PSM 6 format: {e}")
                        # Continue to try other patterns

                # If exact match failed, try the alternative PSM 6 format
                exact_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}\d{3}):(\d{3})', text)
                if exact_match:
                    try:
                        # Extract components manually
                        date_part = exact_match.group(1)
                        time_part = exact_match.group(2)
                        milliseconds = exact_match.group(3)

                        # Split date components
                        day, month, year = date_part.split('/')

                        # Handle the case where minutes and milliseconds are combined
                        hour = time_part[:2]
                        minute = time_part[3:5]
                        second = time_part[5:7]

                        # Create datetime object manually
                        # Convert milliseconds to microseconds correctly
                        microseconds = int(milliseconds)
                        if len(milliseconds) == 4:
                            # For 4-digit milliseconds, treat as 0.xxxx seconds
                            microseconds = int(milliseconds) * 100
                        elif len(milliseconds) > 4:
                            # For longer milliseconds, truncate to 6 digits (microseconds limit)
                            microseconds = int(milliseconds[:6])
                        else:
                            # For 1-3 digit milliseconds, multiply by 1000 to convert to microseconds
                            microseconds = int(milliseconds) * 1000

                        dt = datetime.datetime(
                            int(year), int(month), int(day),
                            int(hour), int(minute), int(second),
                            microseconds
                        )
                        # Store the original format string
                        original_format = f"{date_part} {hour}:{minute}:{second}:{milliseconds}"
                        print(f"Successfully parsed timestamp manually: {dt}")
                        return dt, original_format
                    except (ValueError, IndexError) as e:
                        print(f"Failed to parse exact format: {e}")
                        # Continue to try other patterns

                # Try to match the format where date and time are concatenated without a space (e.g., 13/06/202515:11:56:257)
                exact_match = re.search(r'(\d{2}/\d{2}/\d{4})(\d{2}):(\d{2}):(\d{2}):(\d{3})', text)
                if exact_match:
                    try:
                        # Extract components
                        date_str = exact_match.group(1)  # DD/MM/YYYY
                        hour = exact_match.group(2)
                        minute = exact_match.group(3)
                        second = exact_match.group(4)
                        millisecond = exact_match.group(5)

                        # Split the date
                        day, month, year = date_str.split('/')

                        print(f"Parsed components - Date: {year}-{month}-{day}, Time: {hour}:{minute}:{second}.{millisecond}")

                        # Create datetime object manually
                        # Convert milliseconds to microseconds correctly
                        microseconds = int(millisecond)
                        if len(millisecond) == 4:
                            # For 4-digit milliseconds, treat as 0.xxxx seconds
                            microseconds = int(millisecond) * 100
                        elif len(millisecond) > 4:
                            # For longer milliseconds, truncate to 6 digits (microseconds limit)
                            microseconds = int(millisecond[:6])
                        else:
                            # For 1-3 digit milliseconds, multiply by 1000 to convert to microseconds
                            microseconds = int(millisecond) * 1000

                        dt = datetime.datetime(
                            int(year), int(month), int(day),
                            int(hour), int(minute), int(second),
                            microseconds
                        )
                        # Store the original format string
                        original_format = f"{day}/{month}/{year} {hour}:{minute}:{second}:{millisecond}"
                        print(f"Successfully parsed timestamp manually: {dt}")
                        return dt, original_format
                    except (ValueError, IndexError) as e:
                        print(f"Failed to parse concatenated format: {e}")
                        # Continue to try other patterns

                # If PSM 6 formats failed, continue with existing patterns
                # Try various relaxed patterns
                relaxed_patterns = [
                    # Very relaxed date/time pattern
                    (r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\s+\d{1,2}:\d{1,2}:\d{1,2}[.,]\d{1,3})', None, 3),  # Highest priority
                    # Very relaxed date/time pattern with colon separator for milliseconds
                    (r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\s+\d{1,2}:\d{1,2}:\d{1,2}:\d{1,3})', None, 3),  # Highest priority
                    # Just look for sequences of digits that might be a timestamp
                    (r'(\d{2}[^\d]\d{2}[^\d]\d{2}[^\w]\d{2}[^\d]\d{2}[^\d]\d{2})', None, 2),  # Medium priority
                    # Time only with milliseconds
                    (r'(\d{1,2}:\d{1,2}:\d{1,2}[.,]\d{1,3})', None, 1),  # Low priority
                    # Time only without milliseconds
                    (r'(\d{1,2}:\d{1,2}:\d{1,2})', '%H:%M:%S', 0)  # Lowest priority
                ]

                # Collect all matches from all patterns
                all_matches = []
                for pattern, fmt, priority in relaxed_patterns:
                    matches = re.findall(pattern, text)
                    for match_str in matches:
                        all_matches.append((match_str, fmt, priority))

                # Sort matches by priority (highest first)
                all_matches.sort(key=lambda x: x[2], reverse=True)

                # Process matches in order of priority
                for match_str, fmt, priority in all_matches:
                    print(f"Found potential timestamp with relaxed pattern: {match_str} (priority: {priority})")

                    # Try to normalize the format for parsing
                    normalized_str = match_str
                    for char in ['-', '.']:
                        normalized_str = normalized_str.replace(char, '/')
                    normalized_str = normalized_str.replace(',', '.')
                    # Also replace colon with dot for milliseconds (e.g., 13:28:42:285 -> 13:28:42.285)
                    if ':' in normalized_str:
                        # Find the last colon and replace it with a dot if it's followed by 3 digits (milliseconds)
                        last_colon_index = normalized_str.rfind(':')
                        if last_colon_index != -1 and len(normalized_str) - last_colon_index >= 4:
                            # Check if what follows is 3 digits (milliseconds)
                            if normalized_str[last_colon_index+1:last_colon_index+4].isdigit():
                                normalized_str = normalized_str[:last_colon_index] + '.' + normalized_str[last_colon_index+1:]

                    # Try different date formats
                    formats_to_try = []
                    if fmt:
                        formats_to_try.append(fmt)
                    else:
                        formats_to_try = [
                            # Format with 4-digit year and colon separator for milliseconds (specific format from issue)
                            '%d/%m/%Y %H:%M:%S:%f',  # DD/MM/YYYY HH:MM:SS:ZZZ
                            # Format with 4-digit year and dot separator for milliseconds
                            '%d/%m/%Y %H:%M:%S.%f',
                            # Standard formats
                            '%d/%m/%y %H:%M:%S.%f',
                            '%m/%d/%y %H:%M:%S.%f',
                            '%d/%m/%y %H:%M:%S,%f',
                            '%m/%d/%y %H:%M:%S,%f',
                            '%H:%M:%S.%f',
                            '%H:%M:%S,%f'
                        ]

                    for fmt in formats_to_try:
                        try:
                            if fmt in ['%H:%M:%S.%f', '%H:%M:%S,%f', '%H:%M:%S']:
                                # For time-only format, use today's date
                                time_obj = datetime.datetime.strptime(normalized_str, fmt).time()
                                dt = datetime.datetime.combine(datetime.datetime.today().date(), time_obj)
                            else:
                                dt = datetime.datetime.strptime(normalized_str, fmt)
                            print(f"Successfully parsed timestamp with format {fmt}: {dt}")
                            return dt, normalized_str
                        except ValueError as ve:
                            print(f"Failed to parse with format {fmt}: {ve}")
                            continue
            except Exception as e:
                print(f"Error parsing timestamp pattern: {e}")
                continue
    except Exception as e:
        print(f"OCR error with relaxed pattern: {e}")

    return None, None


def view_video_with_timestamp_overlay(file_path: str) -> tuple[datetime.datetime | None, str | None]:
    """
    Display video with timestamp overlay and allow user to select a reference frame.
    The timestamp overlay is expected to be in the top right corner of the first frame.

    Args:
        file_path: Path to the video file

    Returns:
        Tuple of (selected reference time, original format string) or (None, None) if canceled
    """
    # Open the video file
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not open video file")
        return None

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0  # Default FPS if not available

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Scale video dimensions to a reasonable size while maintaining aspect ratio
    max_display_width = 1280
    max_display_height = 720

    # Calculate scaling factor
    width_scale = max_display_width / original_width if original_width > max_display_width else 1
    height_scale = max_display_height / original_height if original_height > max_display_height else 1
    scale_factor = min(width_scale, height_scale)

    # Apply scaling
    width = int(original_width * scale_factor)
    height = int(original_height * scale_factor)

    # Create a window for the video
    video_window = tk.Toplevel()
    video_window.title("Select Frame with Timestamp Overlay")

    # Calculate window dimensions with minimum sizes to ensure controls are visible
    window_width = max(width + 200, 800)  # Minimum width of 800 pixels
    window_height = max(height + 250, 600)  # Minimum height of 600 pixels

    # Set window size and position it in the center of the screen
    video_window.geometry(f"{window_width}x{window_height}")

    # Center the window on the screen
    screen_width = video_window.winfo_screenwidth()
    screen_height = video_window.winfo_screenheight()
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    video_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Make sure the window is on top initially
    video_window.attributes('-topmost', True)
    video_window.update()
    video_window.attributes('-topmost', False)

    video_window.protocol("WM_DELETE_WINDOW", lambda: on_close())

    # Create a canvas with scrollbar for the main container
    canvas_container = tk.Canvas(video_window)
    canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Add vertical scrollbar to canvas
    scrollbar = tk.Scrollbar(video_window, orient=tk.VERTICAL, command=canvas_container.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas_container.configure(yscrollcommand=scrollbar.set)

    # Create a main container frame to organize all elements
    main_container = tk.Frame(canvas_container)

    # Add the main container to the canvas
    canvas_window = canvas_container.create_window((0, 0), window=main_container, anchor=tk.NW)

    # Configure the canvas to resize with the window
    def configure_canvas(event):
        canvas_container.configure(scrollregion=canvas_container.bbox("all"))
        canvas_container.itemconfig(canvas_window, width=event.width)

    canvas_container.bind("<Configure>", configure_canvas)
    main_container.bind("<Configure>", lambda e: canvas_container.configure(scrollregion=canvas_container.bbox("all")))

    # Make sure scrolling works properly
    def _on_mousewheel(event):
        canvas_container.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas_container.bind_all("<MouseWheel>", _on_mousewheel)

    # Add instruction label at the top of the container
    instruction_label = tk.Label(
        main_container, 
        text="Please locate the timestamp overlay in the top right corner of the video.\n"
             "Navigate to the frame where the timestamp is clearly visible and click 'Select as Reference'.\n"
             "Use the Play/Pause button and arrow buttons below to navigate through the video.",
        wraplength=width,
        justify=tk.LEFT,
        font=("Arial", 10, "bold"),
        fg="blue",
        bg="#f0f0f0",  # Light background for better visibility
        relief=tk.GROOVE,
        borderwidth=1,
        padx=5,
        pady=5
    )
    instruction_label.pack(fill=tk.X, padx=10, pady=10)

    # Create a frame for the video display
    video_frame = tk.Frame(main_container, width=width, height=height)
    video_frame.pack(pady=10)

    # Create a canvas for the video
    canvas = tk.Canvas(video_frame, width=width, height=height, bg="black")
    canvas.pack()

    # Create controls frame with distinct styling to match buttons frame
    controls_frame = tk.Frame(main_container, bg="#e0e0e0", relief=tk.RAISED, borderwidth=2)
    controls_frame.pack(fill=tk.X, padx=10, pady=10)

    # Add a label for the slider
    slider_label = tk.Label(
        controls_frame,
        text="Video Position:",
        font=("Arial", 10, "bold"),
        bg="#e0e0e0"
    )
    slider_label.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=5)

    # Create slider for seeking
    seek_var = tk.IntVar()
    seek_slider = ttk.Scale(
        controls_frame, 
        from_=0, 
        to=total_frames-1, 
        orient=tk.HORIZONTAL,
        variable=seek_var,
        length=width
    )
    seek_slider.pack(fill=tk.X, padx=10, pady=10)

    # Create buttons frame with distinct styling to ensure visibility
    buttons_frame = tk.Frame(main_container, bg="#e0e0e0", relief=tk.RAISED, borderwidth=2)
    buttons_frame.pack(fill=tk.X, padx=10, pady=10)

    # Create info label for current position and timestamp with enhanced visibility
    info_label = tk.Label(
        buttons_frame, 
        text="Frame: 0 / 0  |  Time: 00:00:00.000",
        font=("Arial", 10, "bold"),
        bg="#e0e0e0"  # Match the background of the buttons frame
    )
    info_label.pack(side=tk.LEFT, padx=10, pady=10)

    # Variables to control playback
    playing = False
    current_frame = 0
    reference_time = None
    reference_format = None

    # Function to update the frame display
    def update_frame(frame_number):
        nonlocal current_frame, original_width, original_height

        # Set the position to the requested frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if not ret:
            return False

        current_frame = frame_number
        seek_var.set(frame_number)

        # Calculate timestamp for this frame
        # Using 1970-01-01 as a base time for display purposes
        base_time = datetime.datetime(1970, 1, 1)
        frame_time = base_time + datetime.timedelta(seconds=frame_number / fps)
        timestamp_str = frame_time.strftime("%Y-%m-%d %H:%M:%S.") + f"{frame_time.microsecond // 1000:03d}"

        # Update info label
        info_label.config(text=f"Frame: {frame_number+1} / {total_frames}  |  Time: {timestamp_str}")

        # Add timestamp overlay to the frame
        frame_with_overlay = frame.copy()

        # Highlight the top right corner where the timestamp overlay is expected to be
        # Only do this for the first frame to help the user locate the timestamp
        if frame_number == 0:
            # Calculate the region of interest (ROI) in the top right corner
            # For white text, we need to be more precise with the ROI
            roi_width = int(original_width * 0.4)  # Use 40% of the width for the ROI to ensure we capture the full timestamp
            roi_height = int(original_height * 0.2)  # Use 20% of the height for the ROI to ensure we capture the full timestamp
            roi_x = original_width - roi_width
            roi_y = 0  # Start from the top of the frame

            # Draw a rectangle around the ROI
            cv2.rectangle(
                frame_with_overlay,
                (roi_x, roi_y),
                (roi_x + roi_width, roi_y + roi_height),
                (0, 255, 255),  # Yellow color
                2
            )

            # Add text to indicate this is where the timestamp is expected
            cv2.putText(
                frame_with_overlay,
                "Timestamp Location",
                (roi_x, roi_y + roi_height + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),  # Yellow color
                2
            )

        cv2.putText(
            frame_with_overlay,
            f"Frame: {frame_number+1}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        cv2.putText(
            frame_with_overlay,
            f"Time: {timestamp_str}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Resize the frame to match the scaled dimensions
        if original_width != width or original_height != height:
            frame_with_overlay = cv2.resize(frame_with_overlay, (width, height), interpolation=cv2.INTER_AREA)

        # Convert the frame to RGB (from BGR) and then to a PhotoImage
        rgb_frame = cv2.cvtColor(frame_with_overlay, cv2.COLOR_BGR2RGB)
        img = tk.PhotoImage(data=cv2.imencode('.ppm', rgb_frame)[1].tobytes())

        # Keep a reference to the image to prevent garbage collection
        canvas.image = img
        canvas.create_image(0, 0, anchor=tk.NW, image=img)

        return True

    # Function to play the video
    def play_video():
        nonlocal playing
        if playing:
            return

        playing = True
        play_button.config(text="Pause", command=pause_video)
        play_next_frame()

    # Function to play the next frame
    def play_next_frame():
        nonlocal playing, current_frame

        if not playing:
            return

        if current_frame < total_frames - 1:
            success = update_frame(current_frame + 1)
            if success:
                # Schedule the next frame update based on FPS
                video_window.after(int(1000 / fps), play_next_frame)
            else:
                playing = False
                play_button.config(text="Play", command=play_video)
        else:
            playing = False
            play_button.config(text="Play", command=play_video)

    # Function to pause the video
    def pause_video():
        nonlocal playing
        playing = False
        play_button.config(text="Play", command=play_video)

    # Function to seek to a specific frame
    def on_seek(event=None):
        nonlocal current_frame
        frame_pos = int(seek_var.get())
        if frame_pos != current_frame:
            update_frame(frame_pos)

    # Function to step forward one frame
    def step_forward():
        nonlocal current_frame
        if current_frame < total_frames - 1:
            update_frame(current_frame + 1)

    # Function to step backward one frame
    def step_backward():
        nonlocal current_frame
        if current_frame > 0:
            update_frame(current_frame - 1)

    # Function to select the current frame as reference
    def select_reference():
        nonlocal reference_time

        # Get the current frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Could not read the selected frame")
            return None

        try:
            # Calculate the region of interest (ROI) in the top right corner
            # For white text, we need to be more precise with the ROI
            roi_width = int(original_width * 0.4)  # Use 40% of the width for the ROI to ensure we capture the full timestamp
            roi_height = int(original_height * 0.2)  # Use 20% of the height for the ROI to ensure we capture the full timestamp
            roi_x = original_width - roi_width
            roi_y = 0  # Start from the top of the frame

            # Create a debug visualization of the ROI
            debug_frame = frame.copy()
            cv2.rectangle(
                debug_frame,
                (roi_x, roi_y),
                (roi_x + roi_width, roi_y + roi_height),
                (0, 255, 0),  # Green color
                2
            )
            cv2.putText(
                debug_frame,
                "Timestamp ROI",
                (roi_x, roi_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),  # Green color
                2
            )

            # Save the debug visualization
            import os
            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")
            os.makedirs(debug_dir, exist_ok=True)
            debug_path = os.path.join(debug_dir, "roi_visualization.png")
            cv2.imwrite(debug_path, debug_frame)
            print(f"Saved ROI visualization to {debug_path}")

            # Extract timestamp from the frame using OCR
            extracted_time, original_format = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

            # Inform user about debug images
            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")

            if extracted_time:
                # Use the extracted timestamp
                reference_time = extracted_time
                reference_format = original_format
                messagebox.showinfo(
                    "Reference Frame with Timestamp Selected",
                    f"Selected frame {current_frame+1} with timestamp overlay as reference.\n"
                    f"Successfully extracted timestamp: {reference_time.strftime('%d/%m/%y %H:%M:%S.%f')[:-3]}\n"
                    f"This timestamp will be used as the reference time.\n\n"
                    f"Debug images have been saved to:\n{debug_dir}"
                )
            else:
                # Fallback to calculating the reference time based on the frame number
                # Using 1970-01-01 as a base time
                base_time = datetime.datetime(1970, 1, 1)
                reference_time = base_time + datetime.timedelta(seconds=current_frame / fps)

                messagebox.showwarning(
                    "Timestamp Not Recognized",
                    f"Could not recognize timestamp in the selected frame.\n"
                    f"Please ensure the timestamp is clearly visible in the top right corner.\n"
                    f"Format should be DD/MM/YY HH:MM:ss.SSS\n\n"
                    f"Using generated timestamp as fallback: {reference_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n\n"
                    f"Debug images have been saved to:\n{debug_dir}\n"
                    f"Please check these images to see how the timestamp was processed."
                )

        except Exception as e:
            print(f"Error in select_reference: {e}")
            messagebox.showerror("Error", f"An error occurred while processing the frame: {e}")
            return None

        video_window.destroy()

    # Function to handle window close
    def on_close():
        nonlocal playing
        playing = False
        cap.release()
        video_window.destroy()

    # Create control buttons with enhanced visibility
    play_button = tk.Button(
        buttons_frame, 
        text="Play", 
        command=play_video,
        font=("Arial", 10, "bold"),
        width=8,
        height=2
    )
    play_button.pack(side=tk.LEFT, padx=10, pady=10)

    step_back_button = tk.Button(
        buttons_frame, 
        text="◀", 
        command=step_backward,
        font=("Arial", 12, "bold"),
        width=4,
        height=2
    )
    step_back_button.pack(side=tk.LEFT, padx=10, pady=10)

    step_forward_button = tk.Button(
        buttons_frame, 
        text="▶", 
        command=step_forward,
        font=("Arial", 12, "bold"),
        width=4,
        height=2
    )
    step_forward_button.pack(side=tk.LEFT, padx=10, pady=10)

    select_button = tk.Button(
        buttons_frame, 
        text="Select Frame with Timestamp as Reference", 
        command=select_reference,
        bg="green",
        fg="white",
        font=("Arial", 10, "bold"),
        width=30,
        height=2
    )
    select_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # Bind slider events
    seek_slider.bind("<ButtonRelease-1>", on_seek)

    # Display the first frame
    update_frame(0)

    # Automatically select the first frame as reference
    print("Automatically selecting the first frame as reference")
    select_reference()

    # No need to wait for the window since select_reference() already destroyed it
    # Only wait if the window still exists (wasn't destroyed by select_reference)
    try:
        if video_window.winfo_exists():
            video_window.wait_window()
    except:
        pass  # Window was already destroyed

    # Release resources
    cap.release()

    return reference_time, reference_format


def find_matching_timestamps_in_video(video_path, target_start_time, target_end_time):
    """
    Scan through a video to find frames with timestamps matching the target start and end times.

    Args:
        video_path: Path to the video file to scan
        target_start_time: Target start timestamp to find in the video
        target_end_time: Target end timestamp to find in the video

    Returns:
        Tuple of (start_position, end_position, success) where positions are in seconds from the start of the video,
        and success is a boolean indicating if both timestamps were found
    """
    print(f"Searching for matching timestamps in video: {video_path}")
    print(f"Target start time: {target_start_time}")
    print(f"Target end time: {target_end_time}")

    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return 0, 0, False

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video properties: {total_frames} frames, {fps} fps, duration: {duration:.2f} seconds")

    # Calculate ROI for timestamp extraction
    roi_width = int(width * 0.4)
    roi_height = int(height * 0.2)
    roi_x = width - roi_width
    roi_y = 0

    # Initialize variables
    start_position = None
    end_position = None
    start_frame = None
    end_frame = None

    # Define a time window for matching (allow small differences in timestamps)
    time_window = datetime.timedelta(seconds=1)

    # Use an adaptive sampling approach
    # Start with a coarse sampling interval
    initial_interval = max(1, int(fps * 30))  # Start by sampling every 30 seconds
    min_interval = max(1, int(fps))           # Minimum interval is 1 second

    print(f"Starting with sampling interval: {initial_interval} frames (approx. every {initial_interval/fps:.1f} seconds)")

    # Function to check a specific frame for timestamp
    def check_frame_for_timestamp(frame_num):
        nonlocal start_position, end_position, start_frame, end_frame

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            return None

        timestamp = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)
        if not timestamp:
            return None

        # Check if this timestamp is close to our targets
        start_diff = abs((timestamp - target_start_time).total_seconds())
        end_diff = abs((timestamp - target_end_time).total_seconds())

        # Update start position if this is closer
        if (start_position is None or start_diff < abs((timestamp_at_frame(start_frame) - target_start_time).total_seconds())) and start_diff < time_window.total_seconds():
            print(f"Found better start timestamp: {timestamp} at frame {frame_num}, diff: {start_diff:.3f}s")
            start_position = frame_num / fps
            start_frame = frame_num

        # Update end position if this is closer
        if (end_position is None or end_diff < abs((timestamp_at_frame(end_frame) - target_end_time).total_seconds())) and end_diff < time_window.total_seconds():
            print(f"Found better end timestamp: {timestamp} at frame {frame_num}, diff: {end_diff:.3f}s")
            end_position = frame_num / fps
            end_frame = frame_num

        return timestamp

    # Function to get timestamp at a specific frame (or None if not available)
    def timestamp_at_frame(frame_num):
        if frame_num is None:
            return None

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            return None

        return extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

    # First pass: Coarse search through the entire video
    print("Starting coarse search through the entire video...")
    frame_num = 0
    interval = initial_interval

    # Sample frames throughout the video
    while frame_num < total_frames:
        timestamp = check_frame_for_timestamp(frame_num)

        # If we found a timestamp, adjust our search strategy
        if timestamp:
            # If we're getting close to either target, reduce the interval
            start_diff = abs((timestamp - target_start_time).total_seconds())
            end_diff = abs((timestamp - target_end_time).total_seconds())

            # Adjust interval based on how close we are to targets
            if min(start_diff, end_diff) < 60:  # Within a minute
                new_interval = max(min_interval, int(interval / 2))
                if new_interval != interval:
                    print(f"Getting closer to target, reducing interval to {new_interval} frames")
                    interval = new_interval

        frame_num += interval

    # If we haven't found both timestamps, try a more exhaustive search
    if start_position is None or end_position is None:
        print("Coarse search didn't find all timestamps, trying more exhaustive search...")

        # Try to estimate where the timestamps might be based on video duration
        if total_frames > 0 and fps > 0:
            # If we have some idea of the video's timeline, make educated guesses
            if start_position is None:
                # Try frames at 10%, 25%, 50%, 75% of the video
                for percent in [0.1, 0.25, 0.5, 0.75]:
                    frame_to_check = int(total_frames * percent)
                    print(f"Checking frame at {percent*100}% of video: {frame_to_check}")
                    check_frame_for_timestamp(frame_to_check)
                    if start_position is not None:
                        break

            if end_position is None:
                # Try frames at 25%, 50%, 75%, 90% of the video
                for percent in [0.25, 0.5, 0.75, 0.9]:
                    frame_to_check = int(total_frames * percent)
                    print(f"Checking frame at {percent*100}% of video: {frame_to_check}")
                    check_frame_for_timestamp(frame_to_check)
                    if end_position is not None:
                        break

    # Second pass: Fine-grained search around the found positions
    if start_position is not None:
        # Search more precisely around the start position
        search_radius = int(fps * 5)  # Search 5 seconds around the found position
        search_start = max(0, start_frame - search_radius)
        search_end = min(total_frames, start_frame + search_radius)

        print(f"Refining start timestamp search between frames {search_start} and {search_end}")

        best_start_diff = abs((timestamp_at_frame(start_frame) - target_start_time).total_seconds())
        best_start_pos = start_position
        best_start_frame = start_frame

        for frame_num in range(search_start, search_end):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

            if timestamp:
                diff = abs((timestamp - target_start_time).total_seconds())
                if diff < best_start_diff:
                    best_start_diff = diff
                    best_start_pos = frame_num / fps
                    best_start_frame = frame_num
                    print(f"Better start match: {timestamp} at frame {frame_num}, diff: {diff:.3f}s")

        start_position = best_start_pos
        start_frame = best_start_frame

    if end_position is not None:
        # Search more precisely around the end position
        search_radius = int(fps * 5)  # Search 5 seconds around the found position
        search_start = max(0, end_frame - search_radius)
        search_end = min(total_frames, end_frame + search_radius)

        print(f"Refining end timestamp search between frames {search_start} and {search_end}")

        best_end_diff = abs((timestamp_at_frame(end_frame) - target_end_time).total_seconds())
        best_end_pos = end_position
        best_end_frame = end_frame

        for frame_num in range(search_start, search_end):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

            if timestamp:
                diff = abs((timestamp - target_end_time).total_seconds())
                if diff < best_end_diff:
                    best_end_diff = diff
                    best_end_pos = frame_num / fps
                    best_end_frame = frame_num
                    print(f"Better end match: {timestamp} at frame {frame_num}, diff: {diff:.3f}s")

        end_position = best_end_pos
        end_frame = best_end_frame

    cap.release()

    # If we couldn't find both timestamps, return failure
    if start_position is None or end_position is None:
        print("Could not find matching timestamps in the video")
        return 0, 0, False

    # Ensure start position is before end position
    if start_position >= end_position:
        print(f"Warning: Found start position ({start_position:.3f}s) is after or equal to end position ({end_position:.3f}s)")
        print("This may indicate an issue with timestamp extraction or matching")

        # If the positions are very close or reversed, try to adjust them
        if abs(end_position - start_position) < 1.0:  # Less than 1 second difference
            print("Positions are very close, adding a minimum duration")
            end_position = start_position + 5.0  # Add 5 seconds minimum duration
        elif start_position > end_position:
            print("Swapping start and end positions")
            start_position, end_position = end_position, start_position

    print(f"Final start position: {start_position:.3f}s")
    print(f"Final end position: {end_position:.3f}s")
    print(f"Snippet duration: {end_position - start_position:.3f}s")

    return start_position, end_position, True

def extract_video_snippet(input_video_path, output_video_path, start_time, end_time, reference_time=None):
    """
    Extract a snippet from a video using start and end timestamps.

    This function uses FFmpeg to extract a portion of a video file based on the provided
    timestamps. For MKV files, it uses transcoding with H.264 video and AAC audio codecs.
    For other file types, it first attempts to copy the streams directly, and if that fails,
    it falls back to transcoding.

    Args:
        input_video_path: Path to the input video file
        output_video_path: Path to save the output video snippet
        start_time: Start timestamp as datetime object
        end_time: End timestamp as datetime object
        reference_time: Reference timestamp from the extended video (optional)
                       If provided, it will be used to calculate the offset

    Returns:
        Tuple of (success, error_message) where success is a boolean indicating if the operation
        was successful, and error_message is a string containing any error details (or None if successful)
    """
    try:
        # Verify that end_time is after start_time
        if end_time <= start_time:
            error_msg = "Error: End time must be after start time"
            print(error_msg)
            return False, error_msg

        # Calculate the duration of the snippet
        duration = (end_time - start_time).total_seconds()

        # Search for matching timestamps in the extended video
        start_position, end_position, timestamps_found = find_matching_timestamps_in_video(
            input_video_path, start_time, end_time
        )

        if timestamps_found:
            # Use the found positions
            start_time_str = f"{start_position}"
            duration = end_position - start_position
            print(f"Using found positions: start={start_time_str}, duration={duration}")
        else:
            # Fall back to the previous method
            print("Falling back to reference time method")
            # If reference_time is provided, calculate the offset from the start of the video
            if reference_time:
                # Get the creation time of the input video
                cap = cv2.VideoCapture(input_video_path)
                if not cap.isOpened():
                    error_msg = f"Error: Could not open input video: {input_video_path}"
                    print(error_msg)
                    return False, error_msg

                # Get the first frame to extract timestamp
                ret, first_frame = cap.read()
                if not ret:
                    error_msg = "Error: Could not read the first frame of the input video"
                    print(error_msg)
                    cap.release()
                    return False, error_msg

                # Get dimensions
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                # Calculate ROI for timestamp extraction
                roi_width = int(width * 0.4)
                roi_height = int(height * 0.2)
                roi_x = width - roi_width
                roi_y = 0

                # Extract timestamp from the first frame
                extended_timestamp = extract_timestamp_from_frame(first_frame, roi_x, roi_y, roi_width, roi_height)
                cap.release()

                if extended_timestamp:
                    print(f"Extended video timestamp: {extended_timestamp}")
                    print(f"Start timestamp: {start_time}")

                    # Calculate time offset between the timestamps
                    time_offset = (start_time - extended_timestamp).total_seconds()
                    print(f"Time offset: {time_offset} seconds")

                    # If time_offset is negative, we need to start from the beginning of the video
                    if time_offset < 0:
                        # Use the absolute offset as the start position
                        start_time_str = f"{abs(time_offset)}"
                    else:
                        # Start from the specified offset
                        start_time_str = f"{time_offset}"

                    print(f"Using start position: {start_time_str} seconds")
                else:
                    print("Could not extract timestamp from extended video. Using start_time directly.")
                    # Format the start time for ffmpeg (HH:MM:SS.mmm)
                    start_time_str = start_time.strftime("%H:%M:%S.") + f"{start_time.microsecond // 1000:03d}"
            else:
                # Format the start time for ffmpeg (HH:MM:SS.mmm)
                start_time_str = start_time.strftime("%H:%M:%S.") + f"{start_time.microsecond // 1000:03d}"

        # Normalize file paths for Windows
        input_video_path = os.path.normpath(input_video_path)
        output_video_path = os.path.normpath(output_video_path)

        # Check if ffmpeg is available
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        except FileNotFoundError:
            error_msg = "Error: ffmpeg not found. Please ensure ffmpeg is installed and in your system PATH."
            print(error_msg)
            return False, error_msg
        except subprocess.SubprocessError as se:
            error_msg = f"Error checking ffmpeg: {se}"
            print(error_msg)
            return False, error_msg

        # Check if the input file exists
        if not os.path.exists(input_video_path):
            error_msg = f"Error: Input file not found: {input_video_path}"
            print(error_msg)
            return False, error_msg

        # Check if the output directory exists
        output_dir = os.path.dirname(output_video_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as ose:
                error_msg = f"Error creating output directory: {ose}"
                print(error_msg)
                return False, error_msg

        # Check if the input file is an MKV file or other format that might need special handling
        is_mkv = input_video_path.lower().endswith('.mkv')
        is_mov = input_video_path.lower().endswith('.mov')
        output_ext = os.path.splitext(output_video_path)[1].lower()

        # For better accuracy, use the -ss option before -i for seeking
        # This is more accurate for frame-accurate seeking
        # Use ffmpeg to extract the snippet
        # For MKV/MOV files or when output is MP4, we'll use transcoding to ensure compatibility
        if is_mkv or is_mov or output_ext == '.mp4' or output_ext == '.mov':
            command = [
                "ffmpeg",
                "-ss", start_time_str,  # Put -ss before -i for more accurate seeking
                "-i", input_video_path,
                "-t", str(duration),
                "-c:v", "libx264",  # Use H.264 for video
                "-preset", "medium", # Balance between quality and encoding speed
                "-crf", "23",       # Constant Rate Factor (23 is default, lower is better quality)
                "-c:a", "aac",      # Use AAC for audio
                "-strict", "experimental",
                "-b:a", "192k",     # Audio bitrate
                "-pix_fmt", "yuv420p", # Widely compatible pixel format
                "-movflags", "+faststart", # Optimize for web streaming
                "-map", "0",        # Include all streams from input
                "-avoid_negative_ts", "1", # Handle potential timestamp issues
                "-y",               # Overwrite output file if it exists
                output_video_path
            ]
        else:
            command = [
                "ffmpeg",
                "-ss", start_time_str,  # Put -ss before -i for more accurate seeking
                "-i", input_video_path,
                "-t", str(duration),
                "-c", "copy",       # Copy the codec to avoid re-encoding for non-MKV files
                "-map", "0",        # Include all streams from input
                "-avoid_negative_ts", "1", # Handle potential timestamp issues
                "-y",               # Overwrite output file if it exists
                output_video_path
            ]

        print(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            error_msg = f"Error extracting video snippet: {result.stderr}"
            print(error_msg)
            # If the first attempt failed and we tried to copy streams, try again with transcoding
            if not is_mkv and not is_mov and "-c copy" in " ".join(command):
                print("Attempting to extract with transcoding instead of stream copying...")
                transcode_command = [
                    "ffmpeg",
                    "-ss", start_time_str,  # Put -ss before -i for more accurate seeking
                    "-i", input_video_path,
                    "-t", str(duration),
                    "-c:v", "libx264",  # Use H.264 for video
                    "-preset", "medium", # Balance between quality and encoding speed
                    "-crf", "23",       # Constant Rate Factor (23 is default, lower is better quality)
                    "-c:a", "aac",      # Use AAC for audio
                    "-strict", "experimental",
                    "-b:a", "192k",     # Audio bitrate
                    "-pix_fmt", "yuv420p", # Widely compatible pixel format
                    "-movflags", "+faststart", # Optimize for web streaming
                    "-map", "0",        # Include all streams from input
                    "-avoid_negative_ts", "1", # Handle potential timestamp issues
                    "-y",               # Overwrite output file if it exists
                    output_video_path
                ]
                print(f"Executing command: {' '.join(transcode_command)}")
                result = subprocess.run(transcode_command, capture_output=True, text=True)

                if result.returncode != 0:
                    error_msg = f"Error extracting video snippet with transcoding: {result.stderr}"
                    print(error_msg)
                    return False, error_msg
                else:
                    print(f"Successfully extracted video snippet with transcoding to {output_video_path}")
                    return True, None
            return False, error_msg

        print(f"Successfully extracted video snippet to {output_video_path}")
        return True, None

    except Exception as e:
        error_msg = f"Error extracting video snippet: {e}"
        print(error_msg)
        return False, error_msg

def read_timestamps_from_file(file_path):
    """
    Read the first and last timestamps from a frame_times.txt file.

    Args:
        file_path: Path to the frame_times.txt file

    Returns:
        Tuple of (first_timestamp, last_timestamp) as datetime objects, or (None, None) if file not found or invalid
    """
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None, None

        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row

            # Get the first row (first frame)
            try:
                first_row = next(reader)
                first_frame, first_timestamp_str = first_row
            except StopIteration:
                print("No data rows found in the file")
                return None, None

            # Read all rows to get to the last one
            last_row = first_row
            for row in reader:
                last_row = row

            last_frame, last_timestamp_str = last_row

            # Parse the timestamps (format: YYYYmmdd_HH:MM:SS.LLL)
            try:
                def parse_timestamp(ts_str):
                    # Split into date and time parts
                    date_part, time_part = ts_str.split('_')

                    # Parse date (YYYYmmdd)
                    year = int(date_part[:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])

                    # Parse time (HH:MM:SS.LLL)
                    hour = int(time_part[:2])
                    minute = int(time_part[3:5])
                    second = int(time_part[6:8])

                    # Convert milliseconds to microseconds correctly
                    millisecond_str = time_part[9:]
                    microseconds = int(millisecond_str)
                    if len(millisecond_str) == 4:
                        # For 4-digit milliseconds, treat as 0.xxxx seconds
                        microseconds = int(millisecond_str) * 100
                    elif len(millisecond_str) > 4:
                        # For longer milliseconds, truncate to 6 digits (microseconds limit)
                        microseconds = int(millisecond_str[:6])
                    else:
                        # For 1-3 digit milliseconds, multiply by 1000 to convert to microseconds
                        microseconds = int(millisecond_str) * 1000

                    return datetime.datetime(
                        year, month, day,
                        hour, minute, second,
                        microseconds
                    )

                first_timestamp = parse_timestamp(first_timestamp_str)
                last_timestamp = parse_timestamp(last_timestamp_str)

                return first_timestamp, last_timestamp

            except (ValueError, IndexError) as e:
                print(f"Error parsing timestamps: {e}")
                print(f"First timestamp string: {first_timestamp_str}")
                print(f"Last timestamp string: {last_timestamp_str}")
                return None, None

    except Exception as e:
        print(f"Error reading timestamps file: {e}")
        return None, None

def process_video_file(file_path, root=None, skip_extended_video=False) -> bool:
    """
    Process a single video file to extract timestamps and save them to a frame_times.txt file.

    Args:
        file_path: Path to the video file to process
        root: Tkinter root window (if None, a new one will be created)
        skip_extended_video: Whether to skip the extended video processing

    Returns:
        bool: True if processing was successful, False otherwise
    """
    print(f"Processing video file: {file_path}")

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print(f"Could not open video: {file_path}")
        return False

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print("Invalid FPS detected; defaulting to 30.")
        fps = 30.0

    # Automatically select "Yes" for the reference time method
    reference_method = True
    # For debugging purposes, print that we're automatically selecting "Yes"
    print("Automatically selecting 'Yes' for reference time method (View video and select frame with timestamp overlay)")

    creation = None
    original_format = None

    if reference_method is True:  # Yes - View video
        # Let user view video and select a reference frame
        reference_time, reference_format = view_video_with_timestamp_overlay(file_path)
        if reference_time:
            # Use the full extracted timestamp (including date) as the reference time
            creation = reference_time
            original_format = reference_format

    elif reference_method is False:  # No - Select from metadata
        # Get all metadata
        metadata = get_all_metadata(file_path)

        # Let user select reference time from metadata
        creation = select_reference_time(metadata)

    # If no time selected or canceled, fall back to creation_time or current time
    if creation is None:
        creation = get_creation_time(file_path) or datetime.datetime.now()

    rows = []
    frame = 0
    while True:
        ret, _ = cap.read()
        if not ret:
            break
        frame += 1
        ts = creation + datetime.timedelta(seconds=frame / fps)
        # Format the timestamp using the original format if available, otherwise use the default format
        if original_format and frame == 1:  # For the first frame, use the exact extracted format
            timestamp_str = original_format
        elif original_format:  # For subsequent frames, use the same format but update the time
            # Extract the time components from the timestamp
            if ":" in original_format:  # Format with colons (e.g., HH:MM:SS:mmm)
                parts = original_format.split()
                if len(parts) > 1:  # Has date and time parts
                    date_part = parts[0]
                    time_parts = parts[1].split(":")
                    if len(time_parts) >= 4:  # Format with milliseconds as HH:MM:SS:mmm
                        timestamp_str = f"{date_part} {ts.strftime('%H%M%S')}:{ts.microsecond // 1000:03d}"
                    else:  # Format without milliseconds
                        timestamp_str = f"{date_part} {ts.strftime('%H%M%S')}"
                else:  # Only time part
                    timestamp_str = ts.strftime("%H%M%S")
            else:  # Format with dots (e.g., HH:MM:SS.mmm)
                parts = original_format.split()
                if len(parts) > 1:  # Has date and time parts
                    date_part = parts[0]
                    timestamp_str = f"{date_part} {ts.strftime('%H%M%S')}.{ts.microsecond // 1000:03d}"
                else:  # Only time part
                    timestamp_str = f"{ts.strftime('%H%M%S')}.{ts.microsecond // 1000:03d}"
        else:  # No original format available, use the default format
            timestamp_str = ts.strftime("%Y%m%d_%H%M%S.") + f"{ts.microsecond // 1000:03d}"
        rows.append([frame, timestamp_str])

    cap.release()

    file_path_obj = Path(file_path)
    output_path = file_path_obj.parent / "frame_times.txt"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Frame", "Timestamp"])
        writer.writerows(rows)

    print(f"Saved timestamp chart to {output_path}")

    # Skip the extended video portion if the flag is set
    if skip_extended_video:
        print("Skipping extended video processing as requested.")
        return True

    # Automatically select "No" for the extract video snippet dialog
    extract_snippet = False
    # For debugging purposes, print that we're automatically selecting "No"
    print("Automatically selecting 'No' for Extract Video Snippet dialog")

    return True

def find_video_files(directory, filename="video.avi"):
    """
    Find all video files with the specified filename in the directory and its subdirectories.

    Args:
        directory: The parent directory to search in
        filename: The filename to search for (default: "video.avi")

    Returns:
        list: A list of paths to the found video files
    """
    video_files = []

    # Convert to Path object for easier handling
    directory_path = Path(directory)

    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory_path):
        if filename in files:
            video_path = Path(root) / filename
            video_files.append(str(video_path))

    return video_files

def main(skip_extended_video=False) -> None:
    root = tk.Tk()
    root.withdraw()

    # Ask user to select a directory instead of a file
    directory_path = filedialog.askdirectory(
        title="Select Parent Directory containing video.avi files"
    )

    if not directory_path:
        print("No directory selected.")
        root.destroy()
        return

    # Find all video.avi files in the directory and its subdirectories
    video_files = find_video_files(directory_path)

    if not video_files:
        print(f"No video.avi files found in {directory_path} or its subdirectories.")
        root.destroy()
        return

    print(f"Found {len(video_files)} video.avi files to process.")

    # Process each video file
    successful_count = 0
    failed_count = 0

    for i, video_path in enumerate(video_files):
        print(f"\nProcessing file {i+1}/{len(video_files)}: {video_path}")
        try:
            success = process_video_file(video_path, root, skip_extended_video)
            if success:
                successful_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"Error processing {video_path}: {e}")
            failed_count += 1

    print(f"\nProcessing complete. Successfully processed {successful_count} files. Failed to process {failed_count} files.")
    # Ensure the application terminates properly
    root.destroy()


if __name__ == "__main__":
    import argparse

    # Create argument parser
    parser = argparse.ArgumentParser(description='Process video metadata and optionally extract snippets.')
    parser.add_argument('--skip-extended-video', action='store_true', 
                        help='Skip the extended video processing portion')

    # Parse arguments
    args = parser.parse_args()

    # Call main with the parsed arguments
    main(skip_extended_video=args.skip_extended_video)
