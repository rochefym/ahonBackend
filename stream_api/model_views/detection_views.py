from django.http import Http404
from django.http import HttpResponse, StreamingHttpResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import os
import datetime
import mimetypes

from ultralytics import YOLO
import cv2

from stream_api.models import Detection, Mission, PersonDetectionModel, Victim
from stream_api.serializers import DetectionSerializer


# Load the model once
detection_model = YOLO("best.pt")


#========== DETECTION VIEWS ====================================================================================================
class DetectionList(APIView):
    def get(self, request, format=None):
        detection = Detection.objects.all()
        serializer = DetectionSerializer(detection, many=True)
        return Response(serializer.data)


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


