import mimetypes
from django.http import HttpResponse, StreamingHttpResponse
from django.http import Http404
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from io import BytesIO
import os
import time
import datetime
import json
import base64

from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image

from stream_api.models import Detection, Mission, PersonDetectionModel, Victim
from stream_api.serializers import DetectionSerializer, MissionSerializer, VictimSerializer


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
    API View that streams fine-tuned YOLOv8 detection frames in multipart format
    """

    def get_detection_generator(self):
        """Generator that yields YOLO-annotated frames at ~10 fps"""
        while True:
            try:
                if os.path.exists("image.jpg"):
                    image = cv2.imread("image.jpg")
                else:
                    raise FileNotFoundError("image.jpg not found")

                # results = detection_model(image, conf=0.5, iou=0.75)
                results = detection_model(image, conf=0.5)
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



#====== MISSION VIEWS ========================================================================================================
class MissionList(APIView):
    """
    List all missions, or create a new mission.
    """
    def get(self, request, format=None):
        mission = Mission.objects.all()
        serializer = MissionSerializer(mission, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        try:
            #1. Extract data
            date_time_started = request.data.get('date_time_started', datetime.datetime.now())
            date_time_ended = request.data.get('date_time_ended', None)

            #2. Create the Mission Object manually
            mission = Mission.objects.create(
                date_time_started=date_time_started,
                date_time_ended=date_time_ended
            )

            #3. Serialize the created Mission Object
            mission_serializer = MissionSerializer(mission)
            return Response(mission_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MissionDetail(APIView):
    """
    Retrieve, update or delete a mission instance.
    """
    def get_object(self, pk):
        try:
            return Mission.objects.get(pk=pk)
        except Mission.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        mission = self.get_object(pk)
        serializer = MissionSerializer(mission)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        try:
            #1. Get the mission object
            mission = self.get_object(pk)

            #2. Extract data from PUT request
            date_time_ended = request.data.get('date_time_ended')
            
            #3. Update the mission object
            mission.date_time_ended = date_time_ended
            mission.save()

            return Response(MissionSerializer(mission).data, status=status.HTTP_200_OK)
        except Mission.DoesNotExist:
            return Response({"error": "Mission not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
    def delete(self, request, pk, format=None):
        mission = self.get_object(pk)
        mission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


#========== DETECTION VIEWS ====================================================================================================
class DetectionList(APIView):
    def get(self, request, format=None):
        detection = Detection.objects.all()
        serializer = DetectionSerializer(detection, many=True)
        return Response(serializer.data)

class CaptureDetectionView(APIView):
    """
    API View to capture current detection and save to database
    """
    def post(self, request):
        try:
            # 1. Get required parameters
            mission_id = request.data.get('mission_id')
            person_detection_model_id = request.data.get('person_detection_model_id', 2)
            latitude = request.data.get('latitude', 0.0)
            longitude = request.data.get('longitude', 0.0)
            is_live = request.data.get('is_live', False)

            # 2. Get Mission & PersonDetectionModel objects
            mission = Mission.objects.get(id=mission_id)
            person_detection_model = PersonDetectionModel.objects.get(id=person_detection_model_id)
            
            # 3.1. Check if image exists
            if not os.path.exists("image.jpg"):
                return Response({"error": "No image available to capture"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 3.2. Load and process the image
            image = cv2.imread("image.jpg")
            if image is None:
                return Response({"error": "Failed to load image"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 3.3. Run YOLO detection
            results = detection_model(image, conf=0.5)
            
            # 3.4. Create annotated frame for saving
            annotated_frame = results[0].plot()
            
            # 3.5. Convert annotated frame to bytes for saving
            ret, jpeg_buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                return Response(
                    {"error": "Failed to encode annotated image"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 4. Create Detection object
            detection = Detection.objects.create(
                mission=mission,
                person_detection_model=person_detection_model,
                latitude=latitude,
                longitude=longitude,
                timestamp=datetime.datetime.now(),
                is_live=is_live
            )
            
            # 5. Save the annotated image in the detection object
            image_name = f"detection_id_{detection.id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            detection.snapshot.save(image_name, ContentFile(jpeg_buffer.tobytes()), save=True)
            
            # 6. Process detections and create Victim objects
            victims_created = []

            boxes = results[0].boxes if results[0].boxes is not None else []

            if len(boxes) > 0:
                for i, box in enumerate(boxes):
                    # Extract bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    # Create bounding box dict
                    bounding_box = {
                        'x1': float(x1),
                        'y1': float(y1),
                        'x2': float(x2),
                        'y2': float(y2)
                    }
                    
                    # Generate unique person ID
                    person_id = f"person_{detection.id}_{i+1}"
                    
                    # Create Victim record/object
                    victim = Victim.objects.create(
                        detection=detection,
                        person_id=person_id,
                        person_recognition_confidence=confidence,
                        bounding_box=bounding_box,
                        coco_keypoints={},  # You can add keypoint detection if needed
                        movement_category='unknown',
                        condition='unknown',
                        is_found=False,
                        estimated_latitude=latitude,
                        estimated_longitude=longitude
                    )
                    
                    victims_created.append({
                        'id': victim.id,
                        'person_id': person_id,
                        'confidence': confidence,
                        'bounding_box': bounding_box
                    })
            
            # Serialize the detection for response
            detection_serializer = DetectionSerializer(detection)
            return Response({"victims": victims_created , "data": detection_serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DetectionImageView(APIView):
    """
    API View to serve detection snapshot images
    """
    def get(self, request, detection_id):
        try:
            # Get the detection object
            detection = Detection.objects.get(id=detection_id)
            
            # Check if snapshot exists
            if not detection.snapshot:
                return Response({"error": "No snapshot available for this detection"}, status=status.HTTP_404_NOT_FOUND)
            
            # Get the file path
            image_path = detection.snapshot.path
            
            # Check if file exists on disk
            if not os.path.exists(image_path):
                return Response({"error": "Snapshot file not found on disk"}, status=status.HTTP_404_NOT_FOUND)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(image_path)
            if content_type is None:
                content_type = 'image/jpeg'
            
            # Read and return the image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = HttpResponse(image_data, content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="detection_{detection_id}.jpg"'
            return response
            
        except Detection.DoesNotExist:
            return Response({"error": "Detection not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DetectionDetail(APIView):
    """
    Retrieve, update or delete a Detection instance.
    """
    def get_object(self, pk):
        try:
            return Detection.objects.get(pk=pk)
        except Detection.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        try:
            detection = self.get_object(pk)
            serializer = DetectionSerializer(detection)

             # Add image URL to response
            data = serializer.data
            if detection.snapshot:
                # Build full URL for the image
                image_url = request.build_absolute_uri(f'/api/detection/{pk}/image/')
                data['image_url'] = image_url
            else:
                data['image_url'] = None

            return Response(data, status=status.HTTP_200_OK)
        except Detection.DoesNotExist:
            return Response({"error": "Detection not found"}, status=status.HTTP_404_NOT_FOUND)

        
    def delete(self, request, pk, format=None):
        detection = self.get_object(pk)
        detection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



#======= VICTIMS =======================================================================================================
class VictimsByDetectionView(APIView):
    """
    Get all victims for a specific detection
    """
    def get(self, request, detection_id):
        try:
            # Check if detection exists
            detection = Detection.objects.get(id=detection_id)
            
            # Get all victims for this detection
            victims = Victim.objects.filter(detection=detection)
            
            # Serialize the victims
            serializer = VictimSerializer(victims, many=True)
            
            return Response({
                'detection_id': detection_id,
                'victims_count': len(victims),
                'victims': serializer.data
            })
            
        except Detection.DoesNotExist:
            return Response(
                {"error": "Detection not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class DetectionsByMissionView(APIView):
    """
    Get all detections for a specific mission
    """
    def get(self, request, mission_id):
        try:
            # Check if mission exists
            mission = Mission.objects.get(id=mission_id)
            
            # Get all detections for this mission
            detections = Detection.objects.filter(mission=mission).order_by('-timestamp')
            
            # Serialize the detections
            serializer = DetectionSerializer(detections, many=True)
            
            # Add image URLs to each detection
            detections_data = []
            for detection in detections:
                detection_data = DetectionSerializer(detection).data
                if detection.snapshot:
                    image_url = request.build_absolute_uri(f'/api/detection/{detection.id}/image/')
                    detection_data['image_url'] = image_url
                else:
                    detection_data['image_url'] = None
                detections_data.append(detection_data)
            
            return Response({
                'mission_id': mission_id,
                'detections_count': len(detections),
                'detections': detections_data
            })
            
        except Mission.DoesNotExist:
            return Response(
                {"error": "Mission not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VictimDetailView(APIView):
    """
    Retrieve, update or delete a specific victim
    """
    def get_object(self, pk):
        try:
            return Victim.objects.get(pk=pk)
        except Victim.DoesNotExist:
            raise Http404
    
    def get(self, request, pk, format=None):
        try:
            victim = self.get_object(pk)
            serializer = VictimSerializer(victim)
            return Response(serializer.data)
        except Victim.DoesNotExist:
            return Response(
                {"error": "Victim not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, pk, format=None):
        try:
            victim = self.get_object(pk)
            
            # Update fields that can be modified
            victim.movement_category = request.data.get('movement_category', victim.movement_category)
            victim.risk_category = request.data.get('risk_category', victim.risk_category)
            victim.is_found = request.data.get('is_found', victim.is_found)
            victim.estimated_latitude = request.data.get('estimated_latitude', victim.estimated_latitude)
            victim.estimated_longitude = request.data.get('estimated_longitude', victim.estimated_longitude)
            
            victim.save()
            
            serializer = VictimSerializer(victim)
            return Response(serializer.data)
            
        except Victim.DoesNotExist:
            return Response(
                {"error": "Victim not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, pk, format=None):
        victim = self.get_object(pk)
        victim.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AllVictimsView(APIView):
    """
    Get all victims across all detections
    """
    def get(self, request):
        try:
            victims = Victim.objects.all().order_by('-detection__timestamp')
            serializer = VictimSerializer(victims, many=True)
            return Response({
                'victims_count': len(victims),
                'victims': serializer.data
            })
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )