import csv
import subprocess
import json
import datetime
from pathlib import Path

import cv2
import tkinter as tk
from tkinter import filedialog


def get_creation_time(path: str) -> datetime.datetime | None:
    """Extract creation time from video metadata using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_entries",
            "format_tags=creation_time",
            path,
        ], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        value = data.get("format", {}).get("tags", {}).get("creation_time")
        if value:
            return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        pass
    return None


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select AVI file",
        filetypes=[("AVI files", "*.avi")],
    )
    if not file_path:
        print("No file selected.")
        return

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print("Invalid FPS detected; defaulting to 30.")
        fps = 30.0

    creation = get_creation_time(file_path) or datetime.datetime.now()

    rows = []
    frame = 0
    while True:
        ret, _ = cap.read()
        if not ret:
            break
        frame += 1
        ts = creation + datetime.timedelta(seconds=frame / fps)
        timestamp_str = ts.strftime("%Y%m%d_%H%M%S.") + f"{ts.microsecond // 1000:03d}"
        rows.append([frame, timestamp_str])

    cap.release()

    output_path = Path(file_path).with_suffix("_timestamps.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Frame", "Timestamp"])
        writer.writerows(rows)

    print(f"Saved timestamp chart to {output_path}")


if __name__ == "__main__":
    main()
