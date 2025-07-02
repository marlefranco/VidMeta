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
    cv2.imwrite("test_frame.png", frame)
    print(f"Created test frame with timestamp: {timestamp_text}")
    print(f"ROI coordinates: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
    
    # Extract the timestamp from the frame
    extracted_time = extract_timestamp_from_frame(frame, roi_x, roi_y, roi_width, roi_height)
    
    # Check if the extraction was successful
    if extracted_time:
        print(f"Successfully extracted timestamp: {extracted_time}")
        expected_time = datetime.datetime.strptime(timestamp_text, '%d/%m/%Y %H:%M:%S:%f')
        print(f"Expected timestamp: {expected_time}")
        
        # Compare the extracted timestamp with the expected timestamp
        if extracted_time == expected_time:
            print("PASS: Extracted timestamp matches the expected timestamp")
        else:
            print("FAIL: Extracted timestamp does not match the expected timestamp")
            print(f"Difference: {extracted_time - expected_time}")
    else:
        print("FAIL: Could not extract timestamp from the frame")

if __name__ == "__main__":
    test_timestamp_extraction()