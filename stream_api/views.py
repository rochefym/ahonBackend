from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
from io import BytesIO
import os
import time
from ultralytics import YOLO
import cv2
import numpy as np


# Load the model once
yolo_model = YOLO("best.pt")
# yolo_model.conf = 0.75  # Set confidence threshold (0.0 to 1.0)
# yolo_model.iou = 0.5  # Optional: Set IoU threshold for NMS
# yolo_model.max_det = 300  # Optional: Set maximum detections per image

class YoloDetectionStreamView(APIView):
    """
    API View that streams YOLOv8 detection frames in multipart format
    """

    def get_detection_generator(self):
        """Generator that yields YOLO-annotated frames at ~10 fps"""
        while True:
            try:
                if os.path.exists("image.jpg"):
                    image = cv2.imread("image.jpg")
                else:
                    raise FileNotFoundError("image.jpg not found")

                results = yolo_model(image, conf=0.5)
                annotated_frame = results[0].plot()

                ret, jpeg = cv2.imencode('.jpg', annotated_frame)
                if not ret:
                    raise Exception("Failed to encode image")

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

                time.sleep(0.1)  # ~10 FPS

            except Exception as e:
                print(f"Error streaming image: {e}")
                # Fallback to placeholder image
                try:
                    with open("placeholder.jpg", "rb") as f:
                        image_bytes = f.read()

                    image = Image.open(BytesIO(image_bytes))
                    img_io = BytesIO()
                    image.save(img_io, 'JPEG')
                    img_io.seek(0)
                    img_bytes = img_io.read()

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
                except Exception as fallback_error:
                    print(f"Fallback image error: {fallback_error}")
                    # Yield empty frame if both images fail
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
                time.sleep(0.1)

    def get(self, request):
        return StreamingHttpResponse(
            self.get_detection_generator(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    


class ImageStreamView(APIView):
    """
    API View that streams images in multipart format for live camera feed
    """


    
    def get_image_generator(self):
        SCALE_FACTOR = 0.25  # Adjust this to 0.3 or 0.25 if you want it even smaller

        """Generator function that yields image frames"""
        while True:
            try:
                # Try to read the main image
                if os.path.exists("image.jpg"):
                    with open("image.jpg", "rb") as f:
                        image_bytes = f.read()
                else:
                    raise FileNotFoundError("image.jpg not found")

                # Validate and process image
                image = Image.open(BytesIO(image_bytes))


                # Resize proportionally
                # original_width, original_height = image.size
                # new_width = int(original_width * SCALE_FACTOR)
                # new_height = int(original_height * SCALE_FACTOR)
                # image = image.resize((new_width, new_height))


                img_io = BytesIO()
                image.save(img_io, 'JPEG')
                img_io.seek(0)
                img_bytes = img_io.read()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
                
                # time.sleep(0.9)

            except Exception as e:
                print(f"Error streaming image: {e}")
                # Fallback to placeholder image
                try:
                    with open("placeholder.jpg", "rb") as f:
                        image_bytes = f.read()

                    image = Image.open(BytesIO(image_bytes))


                    # original_width, original_height = image.size
                    # new_width = int(original_width * SCALE_FACTOR)
                    # new_height = int(original_height * SCALE_FACTOR)
                    # image = image.resize((new_width, new_height))

                    img_io = BytesIO()
                    image.save(img_io, 'JPEG')
                    img_io.seek(0)
                    img_bytes = img_io.read()

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
                    
                    # time.sleep(0.9)
                except Exception as fallback_error:
                    print(f"Fallback image error: {fallback_error}")
                    # Yield empty frame if both images fail
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')

    def get(self, request):
        """Stream images as multipart response"""
        response = StreamingHttpResponse(
            self.get_image_generator(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
        return response


class ImageStatusView(APIView):
    """
    API View to check if image exists and get basic info
    """

    def get(self, request):
        """Get status of current image"""
        try:
            if os.path.exists("image.jpg"):
                # Get file size
                file_size = os.path.getsize("image.jpg")

                # Try to get image dimensions
                try:
                    with open("image.jpg", "rb") as f:
                        image = Image.open(f)
                        width, height = image.size

                    return Response({
                        'status': 'available',
                        'file_size': file_size,
                        'dimensions': {
                            'width': width,
                            'height': height
                        }
                    })
                except Exception as e:
                    return Response({
                        'status': 'invalid',
                        'file_size': file_size,
                        'error': str(e)
                    })
            else:
                return Response({
                    'status': 'not_found',
                    'message': 'No image available'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
