import cv2
import numpy as np
import datetime
import os
from pathlib import Path
from vidmeta import extract_timestamp_from_frame

def test_timestamp_alignment():
    """
    Test the timestamp alignment functionality between two videos.

    This script simulates the process of extracting timestamps from two videos
    and calculating the alignment offset between them.
    """
    # Create test frames with timestamps for both videos
    # First video timestamp: 13/06/2025 13:28:42:285
    first_timestamp_text = "13/06/2025 13:28:42:285"
    first_frame = create_test_frame_with_timestamp(first_timestamp_text)

    # Extended video timestamp: 13/06/2025 14:15:30:500 (later time)
    extended_timestamp_text = "13/06/2025 14:15:30:500"
    extended_frame = create_test_frame_with_timestamp(extended_timestamp_text)

    # Save the test frames for visual inspection
    cv2.imwrite("test_first_frame.png", first_frame)
    cv2.imwrite("test_extended_frame.png", extended_frame)

    print(f"Created test frames with timestamps:")
    print(f"First video: {first_timestamp_text}")
    print(f"Extended video: {extended_timestamp_text}")

    # Calculate ROI for timestamp extraction
    height, width, _ = first_frame.shape
    roi_width = int(width * 0.4)
    roi_height = int(height * 0.2)
    roi_x = width - roi_width
    roi_y = 0

    # Extract timestamps from both frames
    first_extracted_time = extract_timestamp_from_frame(first_frame, roi_x, roi_y, roi_width, roi_height)
    extended_extracted_time = extract_timestamp_from_frame(extended_frame, roi_x, roi_y, roi_width, roi_height)

    # Check if extraction was successful
    if first_extracted_time and extended_extracted_time:
        print(f"\nSuccessfully extracted timestamps:")
        print(f"First video: {first_extracted_time}")
        print(f"Extended video: {extended_extracted_time}")

        # Calculate time offset
        time_offset = extended_extracted_time - first_extracted_time
        print(f"\nTime offset between videos: {time_offset.total_seconds():.3f} seconds")

        # Simulate snippet extraction with alignment
        # Let's say we want to extract from 10 seconds to 20 seconds in the first video
        first_start_time = first_extracted_time + datetime.timedelta(seconds=10)
        first_end_time = first_extracted_time + datetime.timedelta(seconds=20)

        print(f"\nOriginal snippet times (from first video):")
        print(f"Start: {first_start_time}")
        print(f"End: {first_end_time}")

        # Adjust times for the extended video
        adjusted_start_time = extended_extracted_time + (first_start_time - first_extracted_time)
        adjusted_end_time = extended_extracted_time + (first_end_time - first_extracted_time)

        print(f"\nAdjusted snippet times (for extended video):")
        print(f"Start: {adjusted_start_time}")
        print(f"End: {adjusted_end_time}")

        # Verify the duration is the same
        original_duration = (first_end_time - first_start_time).total_seconds()
        adjusted_duration = (adjusted_end_time - adjusted_start_time).total_seconds()

        print(f"\nDuration verification:")
        print(f"Original duration: {original_duration:.3f} seconds")
        print(f"Adjusted duration: {adjusted_duration:.3f} seconds")

        if abs(original_duration - adjusted_duration) < 0.001:
            print("PASS: Durations match")
        else:
            print("FAIL: Durations do not match")

        return True
    else:
        if not first_extracted_time:
            print("FAIL: Could not extract timestamp from first frame")
        if not extended_extracted_time:
            print("FAIL: Could not extract timestamp from extended frame")
        return False

def create_test_frame_with_timestamp(timestamp_text):
    """Create a test frame with a timestamp overlay in the top right corner."""
    # Create a black frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Add white text in the top right corner
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(timestamp_text, font, 1, 2)[0]
    text_x = frame.shape[1] - text_size[0] - 20  # 20 pixels from the right edge
    text_y = text_size[1] + 20  # 20 pixels from the top edge

    # Draw white text on black background
    cv2.putText(frame, timestamp_text, (text_x, text_y), font, 1, (255, 255, 255), 2)

    return frame

if __name__ == "__main__":
    test_timestamp_alignment()
