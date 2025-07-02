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
    cv2.imwrite("test_fix_frame.png", frame)
    print(f"Created test frame with timestamp: {timestamp_text}")
    
    # Extract the timestamp from the frame
    extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)
    
    # Check if the extraction was successful
    if extracted_time:
        print(f"Successfully extracted timestamp: {extracted_time}")
        print(f"Year: {extracted_time.year}, Month: {extracted_time.month}, Day: {extracted_time.day}")
        print(f"Hour: {extracted_time.hour}, Minute: {extracted_time.minute}, Second: {extracted_time.second}")
        
        # Check if the date is correct (should be 2025-06-13, not today's date)
        expected_date = datetime.date(2025, 6, 13)
        if extracted_time.date() == expected_date:
            print("SUCCESS: Date is correct!")
        else:
            print(f"ERROR: Date is incorrect. Expected {expected_date}, got {extracted_time.date()}")
    else:
        print("ERROR: Could not extract timestamp from the frame")

if __name__ == "__main__":
    test_timestamp_extraction()