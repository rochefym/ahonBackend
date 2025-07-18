from .detection_views import DetectionList, CaptureDetectionView, DetectionImageView, DetectionDetail, DetectionsByMissionView
from .mission_views import MissionList, MissionDetail
from .victim_views import AllVictimsView, VictimDetailView, VictimsByDetectionView
from .person_detection_model_views import PersonDetectionModelDetail, PersonDetectionModelList

__all__ = [
    DetectionList, CaptureDetectionView, DetectionImageView, DetectionDetail, DetectionsByMissionView,
    MissionList, MissionDetail,
    AllVictimsView, VictimDetailView, VictimsByDetectionView,
    PersonDetectionModelDetail, PersonDetectionModelList,
]