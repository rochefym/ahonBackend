from django.contrib import admin

from stream_api.models import Detection, Mission, PersonDetectionModel, PostureClassification, Victim

# Register your models here.
admin.site.register(Mission)
admin.site.register(PersonDetectionModel)
admin.site.register(Detection)
admin.site.register(Victim)
admin.site.register(PostureClassification)