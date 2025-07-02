# VidMeta

This repository contains a small utility to generate a frame timestamp chart for an AVI file. The tool is written for Python 3.11+ and uses OpenCV and ffprobe.

## Requirements

- Python 3.11 or later
- [OpenCV](https://pypi.org/project/opencv-python/) (`pip install opencv-python`)
- [pytesseract](https://pypi.org/project/pytesseract/) (`pip install pytesseract`)
- [FFmpeg](https://ffmpeg.org/) – `ffprobe` must be available in your `PATH`
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) – Must be installed separately

### Installation Steps

1. Install Python dependencies using pip:

```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
   - **Windows**: Download and install from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: Use Homebrew: `brew install tesseract`
   - **Linux**: Use your package manager: `sudo apt install tesseract-ocr`

3. Ensure Tesseract is in your PATH or set the path in your code:
   - The application now automatically sets the Tesseract path to `C:\Program Files\Tesseract-OCR\tesseract.exe` for Windows users
   - If your Tesseract installation is in a different location, you'll need to modify this path in the `vidmeta.py` file
   - Look for the line: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

## Usage

Run the script and select an `.avi` file when prompted. The program will read the video and offer three options for determining the reference time:

1. **View video and select a frame with timestamp overlay** - This option uses OCR to recognize timestamps in the format `DD/MM/YY HH:MM:ss.SSS` from the top right corner of the video frame.
2. **Select from video metadata** - Choose a timestamp from the video's metadata.
3. **Use default** - Use the video's creation time or the current time.

After selecting a reference time, the program will calculate a timestamp for each frame. The timestamps are formatted as `YYYYmmdd_HHMMSS.LLL` (e.g., "20250613_132842.285"). The frame count starts at `1`.

The output is written to a text file named `frame_times.txt` in comma-separated format in the same directory as the video.

```bash
python vidmeta.py
```

### Video Snippet Extraction

After generating the timestamp file, the program offers the option to extract a snippet from an extended video using the first and last timestamps:

1. The program will ask if you want to extract a snippet from an extended video.
2. If you choose "Yes", it will read the first and last timestamps from the `frame_times.txt` file.
3. It will display these timestamps and prompt you to select the extended video file.
4. Using FFmpeg, it will extract a snippet from the extended video starting at the first timestamp and ending at the last timestamp.
5. The extracted snippet will be saved as `[original_filename]_snippet.[extension]` in the same directory as the extended video.

This feature is useful when you have a longer version of the video and want to extract just the portion that corresponds to the timestamps in the `frame_times.txt` file.

**Note:** This feature requires FFmpeg to be installed and available in your `PATH`.

### Timestamp Recognition

When selecting a frame with timestamp overlay:

1. The program will highlight the top right corner of the first frame where the timestamp is expected to be.
2. Navigate to a frame where the timestamp is clearly visible.
3. Click the "Select Frame with Timestamp as Reference" button.
4. The program will attempt to recognize the timestamp in various formats, including:
   - `DD/MM/YY HH:MM:ss.SSS` (standard format)
   - `DD/MM/YYYY HH:MM:SS:ZZZ` (with 4-digit year and colon separator for milliseconds)
5. If successful, it will use this timestamp (including both date and time components) as the reference time.
6. If unsuccessful, it will fall back to using a calculated timestamp based on the frame number.

#### Enhanced White Text Recognition

The application includes specialized processing for white text timestamp overlays:

1. The timestamp detection is optimized for white text on various backgrounds.
2. Multiple image processing techniques are applied to improve recognition accuracy.
3. Debug images are saved to help diagnose any recognition issues.
4. The Region of Interest (ROI) is sized to ensure complete capture of timestamp text.
5. Various timestamp formats are supported, with flexible pattern matching.

#### Troubleshooting Timestamp Recognition

If the application fails to recognize timestamps:

1. Check the debug images in the `debug_images` folder:
   - `original_roi.png` - The original Region of Interest from the top right corner
   - `gray_roi.png` - The grayscale version of the ROI
   - `preprocess_method_*.png` - Different preprocessing methods applied to the ROI
   - `roi_visualization.png` - Visualization of where the application is looking for the timestamp
   - `final_attempt.png` - The final attempt to recognize the timestamp

2. Verify Tesseract OCR is properly installed and configured:
   - Ensure Tesseract is installed at `C:\Program Files\Tesseract-OCR\` or update the path in the code
   - Check the console output for any Tesseract-related errors

3. Try selecting a different frame where the timestamp is more clearly visible.

## Development

The project was created for Windows 11 and can be opened in PyCharm. No additional configuration is required.
