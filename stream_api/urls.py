"""
URL configuration for camera_stream_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from django.conf.urls.static import static
from django.conf import settings

from . import views
from stream_api.model_views import MissionList, MissionDetail, AllVictimsView, VictimDetailView, VictimsByDetectionView ,PersonDetectionModelDetail, PersonDetectionModelList, DetectionList, CaptureDetectionView, DetectionImageView, DetectionDetail, DetectionsByMissionView

urlpatterns = [
    path('stream/', views.ImageStreamView.as_view(), name='image-stream'),
    path('status/', views.ImageStatusView.as_view(), name='image-status'),
    path('detection-stream/', views.DetectionStreamView.as_view(), name='detection-stream'),

    path('image/', views.SimpleImageView.as_view(), name='simple-image'),

    # Mission URLs
    path('missions/', MissionList.as_view()),
    path('mission/<int:pk>/', MissionDetail.as_view()),

    # Detection URLs
    path('detections/', DetectionList.as_view(), name='detection_list'),
    path('detection/<int:pk>/', DetectionDetail.as_view(), name='detection_detail'),
    path('capture-detection/', CaptureDetectionView.as_view(), name='capture_detection'),
    path('detection/<int:detection_id>/image/', DetectionImageView.as_view(), name='detection-image'),
    # Detections by mission ID
    path('mission/<int:mission_id>/detections/', DetectionsByMissionView.as_view(), name='detections-by-mission'),

    # Victim URLs
    # Victims by detection ID
    path('detection/<int:detection_id>/victims/', VictimsByDetectionView.as_view(), name='victims-by-detection'),
    path('victim/<int:pk>/', VictimDetailView.as_view(), name='victim-detail'),
    path('victims/', AllVictimsView.as_view(), name='all-victims'),

    # Person Detection Model URLs
    path('person-detection-models/', PersonDetectionModelList.as_view(), name='all-person-detection-models'),
    path('person-detection-model/<int:pk>', PersonDetectionModelDetail.as_view(), name='person-detection-model-detail'),
]  

urlpatterns +=  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

