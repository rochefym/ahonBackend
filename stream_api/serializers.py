from rest_framework import serializers
from .models import (
    AhonUser, SARTeam, SARTeamMember, Mission,
    PersonDetectionModel, Detection, Victim, PostureClassification
)

class AhonUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AhonUser
        fields = '__all__'


class SARTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SARTeam
        fields = '__all__'


class SARTeamMemberSerializer(serializers.ModelSerializer):
    user = AhonUserSerializer(read_only=True)
    sar_team = SARTeamSerializer(read_only=True)

    class Meta:
        model = SARTeamMember
        fields = '__all__'


class MissionSerializer(serializers.ModelSerializer):
    sar_team = SARTeamSerializer(read_only=True)
    sar_team_member = AhonUserSerializer(read_only=True)

    class Meta:
        model = Mission
        fields = '__all__'


class PersonDetectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonDetectionModel
        fields = '__all__'


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


class VictimSerializer(serializers.ModelSerializer):
    detection_id = serializers.ReadOnlyField(source='detection.id')
    mission_id = serializers.ReadOnlyField(source='detection.mission.id')

    class Meta:
        model = Victim
        fields = '__all__'


class PostureClassificationSerializer(serializers.ModelSerializer):
    victim = VictimSerializer(read_only=True)

    class Meta:
        model = PostureClassification
        fields = '__all__'
