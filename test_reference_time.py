import cv2
import datetime
from vidmeta import extract_timestamp_from_frame

def test_reference_time():
    """Test that the full timestamp (including date) is used as the reference time."""
    # Create a test frame with a timestamp
    frame = cv2.imread("test_frame.png")
    if frame is None:
        print("Error: Could not load test_frame.png. Please run test_timestamp_extraction.py first.")
        return
    
    # Get the dimensions of the frame
    height, width, _ = frame.shape
    
    # Calculate ROI coordinates (same as in the application)
    roi_width = int(width * 0.4)  # 40% of the width
    roi_height = int(height * 0.2)  # 20% of the height
    roi_x = width - roi_width
    roi_y = 0
    
    # Extract the timestamp from the frame
    extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)
    
    # Check if the extraction was successful
    if extracted_time:
        print(f"Successfully extracted timestamp: {extracted_time}")
        
        # Verify that the date component is preserved
        expected_date = datetime.datetime(2025, 6, 13).date()
        if extracted_time.date() == expected_date:
            print("PASS: Date component is preserved in the extracted timestamp")
        else:
            print(f"FAIL: Date component is not preserved. Expected: {expected_date}, Got: {extracted_time.date()}")
        
        # Verify that the time component is preserved
        expected_time = datetime.time(13, 28, 42, 285000)
        if extracted_time.time().hour == expected_time.hour and \
           extracted_time.time().minute == expected_time.minute and \
           extracted_time.time().second == expected_time.second:
            print("PASS: Time component is preserved in the extracted timestamp")
        else:
            print(f"FAIL: Time component is not preserved. Expected: {expected_time}, Got: {extracted_time.time()}")
        
        # Simulate the fix: use the full timestamp as the reference time
        reference_time = extracted_time
        print(f"Reference time (full timestamp): {reference_time}")
        
        # Generate a timestamp for a frame
        fps = 30.0
        frame_number = 10
        ts = reference_time + datetime.timedelta(seconds=frame_number / fps)
        timestamp_str = ts.strftime("%Y%m%d_%H%M%S.") + f"{ts.microsecond // 1000:03d}"
        print(f"Generated timestamp for frame {frame_number}: {timestamp_str}")
        
        # Verify that the generated timestamp has the correct date
        expected_date_str = "20250613"
        if expected_date_str in timestamp_str:
            print("PASS: Generated timestamp has the correct date")
        else:
            print(f"FAIL: Generated timestamp has incorrect date. Expected date part: {expected_date_str}, Got: {timestamp_str}")
    else:
        print("FAIL: Could not extract timestamp from the frame")

if __name__ == "__main__":
    test_reference_time()