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
        Extracted datetime object or None if no timestamp found
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
        lambda img: cv2.threshold(cv2.GaussianBlur(img, (3, 3), 0), 120, 255, cv2.THRESH_BINARY_INV)[1]
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
                text = pytesseract.image_to_string(
                    processed_img,
                    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789:/.- '
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
                            dt = datetime.datetime(
                                int(year), int(month), int(day),
                                int(hour), int(minute), int(second),
                                int(millisecond) * 1000  # Convert milliseconds to microseconds
                            )
                            print(f"Successfully parsed timestamp manually: {dt}")
                            return dt

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
                        return dt
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
                    config=f'--psm {psm_mode} --oem 3 -c tessedit_char_whitelist=0123456789:/.- '
                )
                print(f"Final attempt with PSM {psm_mode} - Extracted text: {text}")

                # Clean up the text
                text = text.replace('\n', ' ').strip()
            except pytesseract.pytesseract.TesseractError as te:
                print(f"Tesseract Error in final attempt with PSM {psm_mode}: {te}")
                print("This may indicate an issue with Tesseract installation or configuration.")
                print(f"Current Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
                print("Please ensure Tesseract is properly installed and the path is correct.")
                continue  # Try the next PSM mode

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
                        return dt
                    except ValueError:
                        continue
    except Exception as e:
        print(f"OCR error with relaxed pattern: {e}")

    return None


def view_video_with_timestamp_overlay(file_path: str) -> datetime.datetime | None:
    """
    Display video with timestamp overlay and allow user to select a reference frame.
    The timestamp overlay is expected to be in the top right corner of the first frame.

    Args:
        file_path: Path to the video file

    Returns:
        Selected reference time or None if canceled
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
            return

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
        extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

        # Inform user about debug images
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")

        if extracted_time:
            # Use the extracted timestamp
            reference_time = extracted_time
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

    # Wait for the window to close
    video_window.wait_window()

    # Release resources
    cap.release()

    return reference_time


def extract_video_snippet(input_video_path, output_video_path, start_time, end_time):
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

    Returns:
        True if successful, False otherwise
    """
    try:
        # Verify that end_time is after start_time
        if end_time <= start_time:
            print("Error: End time must be after start time")
            return False

        # Calculate the duration of the snippet
        duration = (end_time - start_time).total_seconds()

        # Format the start time for ffmpeg (HH:MM:SS.mmm)
        start_time_str = start_time.strftime("%H:%M:%S.") + f"{start_time.microsecond // 1000:03d}"

        # Check if the input file is an MKV file or other format that might need special handling
        is_mkv = input_video_path.lower().endswith('.mkv')
        output_ext = os.path.splitext(output_video_path)[1].lower()

        # Use ffmpeg to extract the snippet
        # For MKV files or when output is MP4, we'll use transcoding to ensure compatibility
        if is_mkv or output_ext == '.mp4':
            command = [
                "ffmpeg",
                "-i", input_video_path,
                "-ss", start_time_str,
                "-t", str(duration),
                "-c:v", "libx264",  # Use H.264 for video
                "-preset", "medium", # Balance between quality and encoding speed
                "-crf", "23",       # Constant Rate Factor (23 is default, lower is better quality)
                "-c:a", "aac",      # Use AAC for audio
                "-strict", "experimental",
                "-b:a", "192k",     # Audio bitrate
                "-pix_fmt", "yuv420p", # Widely compatible pixel format
                "-movflags", "+faststart", # Optimize for web streaming
                "-y",               # Overwrite output file if it exists
                output_video_path
            ]
        else:
            command = [
                "ffmpeg",
                "-i", input_video_path,
                "-ss", start_time_str,
                "-t", str(duration),
                "-c", "copy",       # Copy the codec to avoid re-encoding for non-MKV files
                "-y",               # Overwrite output file if it exists
                output_video_path
            ]

        print(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error extracting video snippet: {result.stderr}")
            # If the first attempt failed and we tried to copy streams, try again with transcoding
            if not is_mkv and "-c copy" in " ".join(command):
                print("Attempting to extract with transcoding instead of stream copying...")
                transcode_command = [
                    "ffmpeg",
                    "-i", input_video_path,
                    "-ss", start_time_str,
                    "-t", str(duration),
                    "-c:v", "libx264",  # Use H.264 for video
                    "-preset", "medium", # Balance between quality and encoding speed
                    "-crf", "23",       # Constant Rate Factor (23 is default, lower is better quality)
                    "-c:a", "aac",      # Use AAC for audio
                    "-strict", "experimental",
                    "-b:a", "192k",     # Audio bitrate
                    "-pix_fmt", "yuv420p", # Widely compatible pixel format
                    "-movflags", "+faststart", # Optimize for web streaming
                    "-y",               # Overwrite output file if it exists
                    output_video_path
                ]
                print(f"Executing command: {' '.join(transcode_command)}")
                result = subprocess.run(transcode_command, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"Error extracting video snippet with transcoding: {result.stderr}")
                    return False
                else:
                    print(f"Successfully extracted video snippet with transcoding to {output_video_path}")
                    return True
            return False

        print(f"Successfully extracted video snippet to {output_video_path}")
        return True

    except Exception as e:
        print(f"Error extracting video snippet: {e}")
        return False


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

            # Parse the timestamps (format: YYYYmmdd_HHMMSS.LLL)
            try:
                # Split the timestamp into date and time parts
                first_date_part = first_timestamp_str[:8]  # YYYYmmdd
                first_time_part = first_timestamp_str[9:]  # HHMMSS.LLL

                # Parse the date part
                first_year = int(first_date_part[:4])
                first_month = int(first_date_part[4:6])
                first_day = int(first_date_part[6:8])

                # Parse the time part
                first_hour = int(first_time_part[:2])
                first_minute = int(first_time_part[2:4])
                first_second = int(first_time_part[4:6])
                first_millisecond = int(first_time_part[7:])

                # Create datetime object for first timestamp
                first_timestamp = datetime.datetime(
                    first_year, first_month, first_day,
                    first_hour, first_minute, first_second,
                    first_millisecond * 1000  # Convert milliseconds to microseconds
                )

                # Do the same for the last timestamp
                last_date_part = last_timestamp_str[:8]  # YYYYmmdd
                last_time_part = last_timestamp_str[9:]  # HHMMSS.LLL

                # Parse the date part
                last_year = int(last_date_part[:4])
                last_month = int(last_date_part[4:6])
                last_day = int(last_date_part[6:8])

                # Parse the time part
                last_hour = int(last_time_part[:2])
                last_minute = int(last_time_part[2:4])
                last_second = int(last_time_part[4:6])
                last_millisecond = int(last_time_part[7:])

                # Create datetime object for last timestamp
                last_timestamp = datetime.datetime(
                    last_year, last_month, last_day,
                    last_hour, last_minute, last_second,
                    last_millisecond * 1000  # Convert milliseconds to microseconds
                )

                return first_timestamp, last_timestamp

            except (ValueError, IndexError) as e:
                print(f"Error parsing timestamps: {e}")
                return None, None

    except Exception as e:
        print(f"Error reading timestamps file: {e}")
        return None, None


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Video file",
        filetypes=[("Video files", "*.avi;*.mp4;*.mov;*.mkv"), ("All files", "*.*")],
    )
    if not file_path:
        print("No file selected.")
        root.destroy()
        return

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print("Invalid FPS detected; defaulting to 30.")
        fps = 30.0

    # Ask user how they want to select the reference time
    reference_method = messagebox.askyesnocancel(
        "Select Reference Time Method",
        "How would you like to select the reference time?\n\n"
        "Yes: View video and select the frame with timestamp overlay (located in top right corner)\n"
        "No: Select from video metadata\n"
        "Cancel: Use default (creation time or current time)"
    )

    creation = None

    if reference_method is True:  # Yes - View video
        # Let user view video and select a reference frame
        reference_time = view_video_with_timestamp_overlay(file_path)
        if reference_time:
            # Use the full extracted timestamp (including date) as the reference time
            creation = reference_time

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
        # Format the timestamp in the required format YYYYmmdd_HHMMSS.LLL
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

    # Ask the user if they want to extract a snippet from an extended video
    extract_snippet = messagebox.askyesno(
        "Extract Video Snippet",
        "Do you want to extract a snippet from an extended video using the timestamps?"
    )

    if extract_snippet:
        # Read the first and last timestamps from the frame_times.txt file
        first_timestamp, last_timestamp = read_timestamps_from_file(output_path)

        if first_timestamp is None or last_timestamp is None:
            messagebox.showerror(
                "Error",
                "Could not read timestamps from the output file. Please ensure the file exists and contains valid timestamps."
            )
            return

        # Show the timestamps to the user
        messagebox.showinfo(
            "Timestamps",
            f"First timestamp: {first_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
            f"Last timestamp: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n\n"
            f"These timestamps will be used to extract a snippet from the extended video."
        )

        # Ask the user for the extended video file
        extended_video_path = filedialog.askopenfilename(
            title="Select Extended Video file",
            filetypes=[("Video files", "*.avi;*.mp4;*.mov;*.mkv;*.MKV"), ("All files", "*.*")],
        )

        if not extended_video_path:
            print("No extended video file selected.")
            return

        # Generate the output path for the snippet
        extended_video_path_obj = Path(extended_video_path)
        snippet_output_path = extended_video_path_obj.parent / f"{extended_video_path_obj.stem}_snippet{extended_video_path_obj.suffix}"

        # Ask user if they want to align based on the extended video's timestamp
        align_timestamps = messagebox.askyesno(
            "Align Timestamps",
            "Do you want to align timestamps based on the extended video's timestamp overlay?\n\n"
            "This is recommended if the extended video has its own timestamp overlay in the same location as the first video."
        )

        if align_timestamps:
            # Open the extended video to extract its timestamp
            extended_cap = cv2.VideoCapture(extended_video_path)
            if not extended_cap.isOpened():
                messagebox.showerror("Error", "Could not open extended video file")
                return

            # Get the first frame
            ret, extended_frame = extended_cap.read()
            if not ret:
                messagebox.showerror("Error", "Could not read the first frame of the extended video")
                extended_cap.release()
                return

            # Get dimensions
            extended_width = int(extended_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            extended_height = int(extended_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Calculate ROI for timestamp extraction (same as in the first video)
            roi_width = int(extended_width * 0.4)
            roi_height = int(extended_height * 0.2)
            roi_x = extended_width - roi_width
            roi_y = 0

            # Extract timestamp from the extended video's first frame
            extended_timestamp = extract_timestamp_from_frame(extended_frame, roi_x, roi_y, roi_width, roi_height)
            extended_cap.release()

            if extended_timestamp:
                # Calculate the time difference between the two videos
                time_offset = extended_timestamp - first_timestamp

                # Adjust the start and end times for the snippet
                adjusted_start_time = extended_timestamp
                adjusted_end_time = extended_timestamp + (last_timestamp - first_timestamp)

                messagebox.showinfo(
                    "Timestamp Alignment",
                    f"Successfully extracted timestamp from extended video: {extended_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n\n"
                    f"Time offset between videos: {time_offset.total_seconds():.3f} seconds\n\n"
                    f"Adjusted start time: {adjusted_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
                    f"Adjusted end time: {adjusted_end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
                )

                # Extract the snippet with adjusted timestamps
                success = extract_video_snippet(
                    extended_video_path,
                    str(snippet_output_path),
                    adjusted_start_time,
                    adjusted_end_time
                )
            else:
                messagebox.showwarning(
                    "Timestamp Extraction Failed",
                    "Could not extract timestamp from the extended video.\n"
                    "Using timestamps from the first video without alignment."
                )
                # Fall back to using the original timestamps
                success = extract_video_snippet(
                    extended_video_path,
                    str(snippet_output_path),
                    first_timestamp,
                    last_timestamp
                )
        else:
            # Use the original timestamps without alignment
            success = extract_video_snippet(
                extended_video_path,
                str(snippet_output_path),
                first_timestamp,
                last_timestamp
            )

        if success:
            messagebox.showinfo(
                "Success",
                f"Successfully extracted video snippet to:\n{snippet_output_path}"
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to extract video snippet. Please check the console for more details."
            )

    # Ensure the application terminates properly
    root.destroy()


if __name__ == "__main__":
    main()
