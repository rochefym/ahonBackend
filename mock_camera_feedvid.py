import cv2
import time
import sys
import os

def dynamic_camera_feed(video_source):
    """
    Continuously reads frames from a video source (file or camera) and
    saves them as 'image.jpg' to simulate a live feed.

    Args:
        video_source (str or int): Path to a video file or a camera index (e.g., 0).
    """
    # If the source is a number, treat it as a camera index
    try:
        source_is_camera = True
        video_source = int(video_source)
    except ValueError:
        source_is_camera = False

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source '{video_source}'")
        return

    print("Starting dynamic mock camera feed.")
    print(f"   Source: {'Live Camera' if source_is_camera else video_source}")
    print("Press CTRL+C to stop.")

    while True:
        ret, frame = cap.read()
        
        # If the video ends, loop it back to the beginning
        if not ret:
            if not source_is_camera:
                print("🔄 Video ended. Looping back to the beginning.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                print("Error reading from camera.")
                break

        # Save the current frame as image.jpg
        cv2.imwrite("image.jpg", frame)
        
        # Wait a moment before grabbing the next frame to simulate a real-world framerate
        time.sleep(0.5) # ~2 FPS

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mock_camera_feed.py <path_to_video_file_or_camera_index>")
        print("\nExample (Video File): python mock_camera_feed.py \"C:\\videos\\thermal.mp4\"")
        print("Example (Live Camera): python mock_camera_feed.py 0")
    else:
        source = sys.argv[1]
        dynamic_camera_feed(source)