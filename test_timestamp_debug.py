import cv2
import numpy as np
import datetime
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

def test_timestamp_extraction():
    """Test the timestamp extraction function with the specific format."""
    # Create a test frame with the timestamp
    timestamp_text = "13/06/2025 13:28:42:285"
    frame, roi_x, roi_y, roi_width, roi_height = create_test_frame_with_timestamp(timestamp_text)
    
    # Save the test frame for visual inspection
    cv2.imwrite("test_frame_debug.png", frame)
    print(f"Created test frame with timestamp: {timestamp_text}")
    print(f"ROI coordinates: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
    
    # Extract the timestamp from the frame
    extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)
    
    # Check if the extraction was successful
    if extracted_time:
        print(f"Successfully extracted timestamp: {extracted_time}")
        print(f"Extracted components: Year={extracted_time.year}, Month={extracted_time.month}, Day={extracted_time.day}, Hour={extracted_time.hour}, Minute={extracted_time.minute}, Second={extracted_time.second}, Microsecond={extracted_time.microsecond}")
        
        # Simulate the timestamp generation for a frame
        fps = 30.0
        frame_number = 10
        ts = extracted_time + datetime.timedelta(seconds=frame_number / fps)
        timestamp_str = ts.strftime("%Y%m%d_%H%M%S.") + f"{ts.microsecond // 1000:03d}"
        print(f"Generated timestamp for frame {frame_number}: {timestamp_str}")
        print(f"Generated components: Year={ts.year}, Month={ts.month}, Day={ts.day}, Hour={ts.hour}, Minute={ts.minute}, Second={ts.second}, Microsecond={ts.microsecond}")
        
        # Expected timestamp components
        expected_year = 2025
        expected_month = 6
        expected_day = 13
        expected_hour = 13
        expected_minute = 28
        expected_second = 42
        expected_millisecond = 285
        
        # Check if the extracted components match the expected values
        if (extracted_time.year == expected_year and 
            extracted_time.month == expected_month and 
            extracted_time.day == expected_day and 
            extracted_time.hour == expected_hour and 
            extracted_time.minute == expected_minute and 
            extracted_time.second == expected_second and 
            extracted_time.microsecond == expected_millisecond * 1000):
            print("PASS: All timestamp components match the expected values")
        else:
            print("FAIL: Some timestamp components do not match the expected values")
            print(f"Expected: Year={expected_year}, Month={expected_month}, Day={expected_day}, Hour={expected_hour}, Minute={expected_minute}, Second={expected_second}, Microsecond={expected_millisecond * 1000}")
            print(f"Actual: Year={extracted_time.year}, Month={extracted_time.month}, Day={extracted_time.day}, Hour={extracted_time.hour}, Minute={extracted_time.minute}, Second={extracted_time.second}, Microsecond={extracted_time.microsecond}")
    else:
        print("FAIL: Could not extract timestamp from the frame")

if __name__ == "__main__":
    test_timestamp_extraction()