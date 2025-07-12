from django.db import models

class AhonUser(models.Model):
    name = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AhonUser ID: {self.id}"
    

class SARTeam(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SAR Team ID: {self.id}"
    

class SARTeamMember(models.Model):
    user = models.ForeignKey(AhonUser, on_delete=models.CASCADE)
    sar_team = models.ForeignKey(SARTeam, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sar_team')

    def __str__(self):
        return f"SAR Team Member ID: {self.id} - User: {self.user.name} in Team: {self.sar_team.name}"
    

class Mission(models.Model):
    sar_team = models.ForeignKey(SARTeam, on_delete=models.CASCADE)
    sar_team_member = models.ForeignKey(AhonUser, on_delete=models.CASCADE)
    date_time_started = models.DateTimeField()
    date_time_ended = models.DateTimeField(blank=True, null=True)
    

    def __str__(self):
        return f"Mission ID: {self.id}"
    

class PersonDetectionModel(models.Model):
    model_type = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return f"Model ID: {self.id} - Name: {self.model_type}"
    

class Detection(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    person_detection_model = models.ForeignKey(PersonDetectionModel, on_delete=models.CASCADE, default=2)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_live = models.BooleanField(default=False)
    snapshot = models.ImageField(blank=True, null=True)

    def __str__(self):
        return f"Detection ID: {self.id} for Mission ID: {self.mission.id}"
    

class Victim(models.Model):
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE)
    person_id = models.CharField(max_length=100, unique=True)
    person_recognition_confidence = models.FloatField()
    bounding_box = models.JSONField()  # Assuming bounding box is stored as a JSON object
    coco_keypoints = models.JSONField()  # Assuming COCO keypoints are stored as a JSON object
    movement_category = models.CharField(max_length=50, blank=True, null=True, default='unknown')
    risk_category = models.CharField(max_length=50, blank=True, null=True, default='unknown')
    is_found = models.BooleanField(default=False)
    estimated_longitude = models.FloatField(blank=True, null=True, default=0.0)
    estimated_latitude = models.FloatField(blank=True, null=True, default=0.0)

    def __str__(self):
        return f"Victim ID: {self.id} for Detection ID: {self.detection.id}"
    

class PostureClassification(models.Model):
    victim = models.ForeignKey(Victim, on_delete=models.CASCADE)
    posture = models.CharField(max_length=50, default='unknown')  # e.g., 'standing', 'lying', etc.
    confidence = models.FloatField(default=0.0)

    def __str__(self):
        return f"Posture Classification ID: {self.id} for Victim ID: {self.victim.id}"