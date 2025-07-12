from django.contrib import admin

from stream_api.models import AhonUser, Detection, Mission, PersonDetectionModel, PostureClassification, SARTeam, SARTeamMember, Victim

# Register your models here.
admin.site.register(AhonUser)
admin.site.register(SARTeam)
admin.site.register(SARTeamMember)
admin.site.register(Mission)
admin.site.register(PersonDetectionModel)
admin.site.register(Detection)
admin.site.register(Victim)
admin.site.register(PostureClassification)