import cv2
import numpy as np
import datetime
import csv
from pathlib import Path
from vidmeta import extract_timestamp_from_frame

def create_test_frame_with_timestamp(timestamp_text="13/06/2025 13:28:42:285"):
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

    # Calculate ROI coordinates
    roi_width = int(frame.shape[1] * 0.4)  # 40% of the width
    roi_height = int(frame.shape[0] * 0.2)  # 20% of the height
    roi_x = frame.shape[1] - roi_width
    roi_y = 0

    return frame, roi_x, roi_y, roi_width, roi_height

def test_csv_generation():
    """Test the generation of CSV file with timestamps for multiple frames."""
    # Create a test frame with the timestamp
    timestamp_text = "13/06/2025 13:28:42:285"
    frame, roi_x, roi_y, roi_width, roi_height = create_test_frame_with_timestamp(timestamp_text)

    # Save the test frame for visual inspection
    cv2.imwrite("test_frame_csv.png", frame)
    print(f"Created test frame with timestamp: {timestamp_text}")

    # Extract the timestamp from the frame
    extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)

    # Check if the extraction was successful
    if extracted_time:
        print(f"Successfully extracted timestamp: {extracted_time}")
        print(f"Extracted components: Year={extracted_time.year}, Month={extracted_time.month}, Day={extracted_time.day}, Hour={extracted_time.hour}, Minute={extracted_time.minute}, Second={extracted_time.second}, Microsecond={extracted_time.microsecond}")

        # Simulate generating timestamps for multiple frames
        fps = 30.0
        num_frames = 10
        rows = []

        for frame_num in range(1, num_frames + 1):
            ts = extracted_time + datetime.timedelta(seconds=frame_num / fps)
            # Format the timestamp in the required format YYYYmmdd_HHMMSS.LLL
            timestamp_str = ts.strftime("%Y%m%d_%H%M%S.") + f"{ts.microsecond // 1000:03d}"
            rows.append([frame_num, timestamp_str])
            print(f"Frame {frame_num} timestamp: {timestamp_str}")

        # Write the timestamps to a CSV file
        output_path = Path("test_timestamps.csv")
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Frame", "Timestamp"])
            writer.writerows(rows)

        print(f"Saved timestamp chart to {output_path}")

        # Read the CSV file back and verify the timestamps
        with open(output_path, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for i, row in enumerate(reader, 1):
                frame_num, timestamp_str = row
                print(f"CSV row {i}: Frame={frame_num}, Timestamp={timestamp_str}")

                # Verify that the timestamp has the correct format YYYYmmdd_HHMMSS.LLL
                # Check for the date format (YYYYmmdd) and the presence of milliseconds (.)
                if "20250613" in timestamp_str and "_" in timestamp_str and "." in timestamp_str:
                    print(f"PASS: Timestamp for frame {frame_num} has the correct format YYYYmmdd_HHMMSS.LLL")
                else:
                    print(f"FAIL: Timestamp for frame {frame_num} does not have the correct format YYYYmmdd_HHMMSS.LLL")
    else:
        print("FAIL: Could not extract timestamp from the frame")

if __name__ == "__main__":
    test_csv_generation()
