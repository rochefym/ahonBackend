from rest_framework import serializers
from .models import ( Mission, PersonDetectionModel, Detection, Victim, PostureClassification)




class PersonDetectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonDetectionModel
        fields = '__all__'

class VictimSerializer(serializers.ModelSerializer):
    detection_id = serializers.ReadOnlyField(source='detection.id')
    mission_id = serializers.ReadOnlyField(source='detection.mission.id')

    class Meta:
        model = Victim
        fields = '__all__'

class MissionSerializer(serializers.ModelSerializer):
    victims = VictimSerializer(many=True, read_only=True, source='victim_set') # Nested victims
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    victims_found = serializers.SerializerMethodField()
    class Meta:
        model = Mission
        fields = [
            'id', 'mission_id_str', 'status', 'date_time_started', 'date_time_ended',
            'duration', 'detection_model', 'confidence_threshold', 'total_detections',
            'average_confidence', 'temperature_range', 'victims_found', 'victims'
        ]


    def get_status(self, obj):
        if obj.date_time_ended:
            return "Completed" # Or "Aborted" based on another field
        return "In Progress"

    def get_duration(self, obj):
        if not obj.date_time_ended:
            return "0m"
        duration_delta = obj.date_time_ended - obj.date_time_started
        minutes = duration_delta.total_seconds() / 60
        if minutes < 60:
            return f"{round(minutes)}m"
        else:
            hours = int(minutes / 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"

    def get_victims_found(self, obj):
        return obj.victim_set.count()     

class DetectionSerializer(serializers.ModelSerializer):
    mission = MissionSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Detection
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.snapshot and request:
            return request.build_absolute_uri(f'/api/detection/{obj.id}/image/')
        return None 


class PostureClassificationSerializer(serializers.ModelSerializer):
    victim = VictimSerializer(read_only=True)

    class Meta:
        model = PostureClassification
        fields = '__all__'
