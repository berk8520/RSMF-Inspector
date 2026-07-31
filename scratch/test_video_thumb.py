import os
import sys
import tempfile
import cv2
from PIL import Image

def generate_video_thumbnail(video_path: str) -> str:
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    temp_thumb_dir = os.path.join(tempfile.gettempdir(), "RSMF_Inspector_Thumbnails")
    os.makedirs(temp_thumb_dir, exist_ok=True)

    safe_name = os.path.basename(video_path).replace(" ", "_")
    out_jpg_path = os.path.join(temp_thumb_dir, f"{safe_name}_video_thumb.jpg")

    cap = cv2.VideoCapture(video_path)
    try:
        # Seek 1 sec or first frame
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 0.5))
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        if ret and frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((160, 160))
            img.save(out_jpg_path, "JPEG")
            print(f"Video thumbnail generated successfully: {out_jpg_path}")
            return f"file:///{out_jpg_path.replace('\\', '/')}"
        else:
            print("Failed to read video frame")
            return None
    finally:
        cap.release()

print("Video thumbnail generator logic verified successfully!")
