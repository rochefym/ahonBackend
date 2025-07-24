import mimetypes
from django.http import HttpResponse, StreamingHttpResponse
from django.http import Http404

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from io import BytesIO
import os
import time

from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image

from stream_api.models import PersonDetectionModel


# Load the model once
detection_model = YOLO("best.pt")

class SimpleImageView(APIView):
    """
    API View to serve the current image.jpg file directly
    """
    def get(self, request):
        try:
            # Check if image exists
            if not os.path.exists("image.jpg"):
                return Response(
                    {"error": "Image not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determine content type
            content_type, _ = mimetypes.guess_type("image.jpg")
            if content_type is None:
                content_type = 'image/jpeg'
            
            # Read and return the image
            with open("image.jpg", 'rb') as f:
                image_data = f.read()
            
            response = HttpResponse(image_data, content_type=content_type)
            response['Content-Disposition'] = 'inline; filename="image.jpg"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#======== STREAM VIEWS ========================================================================================================
class DetectionStreamView(APIView):
    """
    API View that streams fine-tuned YOLO detection frames in multipart format
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_model = None
        self.current_model_id = None
        self.current_confidence = 0.5
        
    def get_selected_model(self):
        """Get the currently selected model from database"""
        models = PersonDetectionModel.objects.all()
        
        # Find the model with is_selected=True
        for model in models:
            if model.is_selected:
                return model
        
        # If no model is selected, return default (ID=2)
        return PersonDetectionModel.objects.get(id=2)
    
    def get_model_path(self, model_type):
        """Map model type to file path"""
        model_paths = {
            'Top View': 'ai_models/top_view/best.pt',
            'Front/Side View': 'ai_models/front_side_view/best.pt',
            'Angled View': 'ai_models/angled_view/best.pt'
        }
        return model_paths.get(model_type, 'ai_models/front_side_view/best.pt')
    
    def load_detection_model(self):
        """Load the selected detection model"""
        selected_model = self.get_selected_model()
        
        # Check if we need to reload the model
        if (self.current_model is None or self.current_model_id != selected_model.id):
            model_path = self.get_model_path(selected_model.model_type)
            
            if os.path.exists(model_path):
                print(f"Loading model: {selected_model.model_type} from {model_path}")
                self.current_model = YOLO(model_path)
                self.current_model_id = selected_model.id
                self.current_confidence = selected_model.confidence
                print(f"Model loaded successfully with confidence: {self.current_confidence}")
            else:
                print(f"Model file not found: {model_path}")
                # Fallback to default model
                fallback_path = 'ai_models/front_side_view/best.pt'
                if os.path.exists(fallback_path):
                    self.current_model = YOLO(fallback_path)
                    self.current_model_id = selected_model.id
                    self.current_confidence = selected_model.confidence
                else:
                    raise FileNotFoundError("No valid model files found")
                
        # Update confidence if it changed
        if self.current_confidence != selected_model.confidence:
            self.current_confidence = selected_model.confidence
            print(f"Updated confidence to: {self.current_confidence}")

        return self.current_model, self.current_confidence
    

    def get_detection_generator(self):
        """Generator that yields YOLO-annotated frames at ~10 fps"""
        while True:
            try:
                # Load/reload model if needed
                detection_model, confidence = self.load_detection_model()
                
                if os.path.exists("image.jpg"):
                    image = cv2.imread("image.jpg")
                else:
                    raise FileNotFoundError("image.jpg not found")
                
                # Use dynamic confidence from database
                results = detection_model(image, conf=confidence)
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
                        'dimensions': { 'width': width, 'height': height }
                    })
                except Exception as e:
                    return Response({ 'status': 'invalid', 'file_size': file_size, 'error': str(e) })
            else:
                return Response({'status': 'not_found', 'message': 'No image available' }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({ 'status': 'error', 'message': str(e) }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# ==============================================================================
# ADD THE NEW PERSON COUNT VIEW BELOW
# ==============================================================================
from django.http import JsonResponse
from django.conf import settings
import supervision as sv

# Load the general-purpose YOLOv8n model specifically for this counting task
# This uses the yolov8n.pt model you already have in the ai_models/yolo/ directory
try:
    PERSON_COUNT_MODEL_PATH = os.path.join(settings.BASE_DIR, 'ai_models', 'yolo', 'yolov8n.pt')
    person_count_model = YOLO(PERSON_COUNT_MODEL_PATH)
except Exception as e:
    print(f"Error loading yolov8n.pt model: {e}")
    person_count_model = None

@api_view(['GET'])
def get_person_count(request):
    """
    Reads the current 'image.jpg', counts the people detected,
    and returns the count as a JSON response.
    """
    if person_count_model is None:
        return JsonResponse({"error": "Person count model could not be loaded"}, status=500)

    image_path = "image.jpg"
    if not os.path.exists(image_path):
        # If no image is available, it's safe to say the count is 0.
        return JsonResponse({"person_count": 0})

    try:
        # Read the image file that is being updated by your ESP32 stream
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError("Failed to read image file, it might be corrupted or empty.")

        # Perform object detection
        result = person_count_model(frame, agnostic_nms=True)[0]
        detections = sv.Detections.from_ultralytics(result)

        # Filter for persons only (class_id 0 in COCO dataset)
        person_detections = detections[detections.class_id == 0]

        # Get the final count
        person_count = len(person_detections)

        return JsonResponse({"person_count": person_count})

    except Exception as e:
        print(f"An error occurred during person counting: {str(e)}")
        return JsonResponse({"error": "An error occurred during processing."}, status=500)
