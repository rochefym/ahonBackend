import shutil
import time
import sys

def mock_camera_feed(source_image_path):
    """
    Continuously copies a source image to 'image.jpg' to simulate
    a live camera feed for testing purposes.

    Args:
        source_image_path (str): The path to the sample image you want to use.
    """
    destination_path = "image.jpg"
    print(f" Starting mock camera feed.")
    print(f"   Source image: {source_image_path}")
    print(f"   Destination: {destination_path}")
    print("Press CTRL+C to stop the script.")

    try:
        while True:
            shutil.copy(source_image_path, destination_path)
            # Optional: print a message to show it's working
            # print(f"Updated '{destination_path}' at {time.ctime()}")
            time.sleep(2)  # Pauses for 2 seconds to simulate a new frame
    except FileNotFoundError:
        print(f" ERROR: The source file was not found at '{source_image_path}'")
        print("Please check the path and try again.")
    except KeyboardInterrupt:
        print("\n Mock camera feed stopped.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mock_camera_feed.py <path_to_source_image>")
    else:
        source_image = sys.argv[1]
        mock_camera_feed(source_image)