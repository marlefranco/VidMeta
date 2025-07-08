# Process Single Video Script

This script provides a simplified interface for processing a single video file using the functionality from the main vidmeta.py script.

## Usage

```bash
python process_single_video.py [--skip-extended-video] [<video_file_path>]
```

If no video_file_path is provided, a file browser will open to select the video file.

### Arguments

- `video_file_path`: Path to the video file to process (optional)
- `--skip-extended-video`: Optional flag to skip the extended video processing portion

### Example

```bash
python process_single_video.py C:\path\to\your\video.avi
```

Or to skip extended video processing:

```bash
python process_single_video.py --skip-extended-video C:\path\to\your\video.avi
```

Or to use the file browser to select a video file:

```bash
python process_single_video.py
```

## Output

The script will process the specified video file and save a `frame_times.txt` file in the same directory as the video file. This file contains a timestamp chart for each frame in the video.

## Requirements

This script requires the same dependencies as the main vidmeta.py script:
- Python 3.6+
- OpenCV (cv2)
- NumPy
- Tkinter
- Pytesseract

Make sure you have these dependencies installed before running the script.
