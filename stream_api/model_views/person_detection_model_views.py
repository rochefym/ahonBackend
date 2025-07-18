from django.http import Http404

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from stream_api.models import PersonDetectionModel
from stream_api.serializers import PersonDetectionModelSerializer


class PersonDetectionModelList(APIView):
    """
    List all Person Detection Models, or create a new Person Detection Model.
    """
    def get(self, request, format=None):
        person_detection_models = PersonDetectionModel.objects.all()
        serializer = PersonDetectionModelSerializer(person_detection_models, many=True)
        return Response(serializer.data)
    
    def post(self, request, format=None):
        serializer = PersonDetectionModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PersonDetectionModelDetail(APIView):
    """
    Retrieve, update or delete a PersonDetectionModel instance.
    """
    def get_object(self, pk):
        try:
            return PersonDetectionModel.objects.get(pk=pk)
        except PersonDetectionModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        person_detection_model = self.get_object(pk)
        serializer = PersonDetectionModelSerializer(person_detection_model)
        return Response(serializer.data)
    
    # Updates the is_selected field based on the user preference of model to use
    def put(self, request, pk, format=None):
        try:
            # 1. Change selected person_detection_model is_selected = true
            # 1.1. Get the person_detection_model object
            person_detection_model = self.get_object(pk)

            # 1.2. Update the selected person_detection_model object
            person_detection_model.is_selected = True
            person_detection_model.save()

            # 2. Change non-selected person_detection_model objects is_selected = false
            # Only update others if this model is being selected
            PersonDetectionModel.objects.exclude(pk=pk).update(is_selected=False)

            # 3. Update the confidence threshold for all person_detection_model objects
            # 3.1. Get confidence from request body
            conf = request.data.get('confidence')
            conf = float(conf)

            # 3.2. Set confidence threshold for all models
            PersonDetectionModel.objects.all().update(confidence = conf)

            return Response(PersonDetectionModelSerializer(person_detection_model).data, status=status.HTTP_200_OK)
        except PersonDetectionModel.DoesNotExist:
            return Response({"error": "PersonDetectionModel not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        person_detection_model = self.get_object(pk)
        person_detection_model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)