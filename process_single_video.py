#!/usr/bin/env python
"""
Process Single Video Script

This script provides a simplified interface for processing a single video file
using the functionality from the main vidmeta.py script.

Usage:
    python process_single_video.py [--skip-extended-video] [<video_file_path>]

If no video_file_path is provided, a file browser will open to select the video file.
"""

import argparse
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

# Import the necessary function from the main script
from vidmeta import process_video_file

def main():
    """
    Main function to process a single video file.
    """
    # Create argument parser
    parser = argparse.ArgumentParser(description='Process a single video file to extract timestamps.')
    parser.add_argument('video_path', nargs='?', help='Path to the video file to process (optional)')
    parser.add_argument('--skip-extended-video', action='store_true', 
                        help='Skip the extended video processing portion')

    # Parse arguments
    args = parser.parse_args()

    # Create a Tkinter root window (hidden)
    root = tk.Tk()
    root.withdraw()

    # Get video path from command line or file browser
    video_path = args.video_path
    if not video_path:
        # No path provided, open file browser
        video_path = filedialog.askopenfilename(
            title="Select Video file",
            filetypes=[("Video files", "*.avi;*.mp4;*.mov;*.mkv"), ("All files", "*.*")]
        )
        if not video_path:
            print("No file selected.")
            return 1

    # Validate the video path
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return 1

    try:
        print(f"Processing video file: {video_path}")

        # Process the video file
        success = process_video_file(
            video_path, 
            root=root, 
            skip_extended_video=args.skip_extended_video
        )

        if success:
            print(f"Successfully processed video file: {video_path}")
            # Get the output path (same directory as the video file)
            output_path = Path(video_path).parent / "frame_times.txt"
            print(f"Timestamp chart saved to: {output_path}")
            return 0
        else:
            print(f"Failed to process video file: {video_path}")
            return 1
    except Exception as e:
        print(f"Error processing video file: {e}")
        return 1
    finally:
        # Ensure the application terminates properly
        root.destroy()

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
