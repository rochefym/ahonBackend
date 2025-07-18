from django.http import Http404

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import datetime

from stream_api.models import Mission
from stream_api.serializers import MissionSerializer


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
    
