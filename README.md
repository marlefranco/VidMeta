# VidMeta

This repository contains a small utility to generate a frame timestamp chart for an AVI file. The tool is written for Python 3.11+ and uses OpenCV and ffprobe.

## Requirements

- Python 3.11 or later
- [OpenCV](https://pypi.org/project/opencv-python/) (`pip install opencv-python`)
- [FFmpeg](https://ffmpeg.org/) – `ffprobe` must be available in your `PATH`

Install the Python dependency using pip:

```bash
pip install -r requirements.txt
```

## Usage

Run the script and select an `.avi` file when prompted. The program will read the video, determine the creation time from metadata (if available) and calculate a timestamp for each frame. The timestamps are formatted as `YYYYMMDD_hhmmss.SSS` and the frame count starts at `1`.

The output is written to a CSV file named `<video>_timestamps.csv` in the same directory as the video.

```bash
python vidmeta.py
```

## Development

The project was created for Windows 11 and can be opened in PyCharm. No additional configuration is required.
