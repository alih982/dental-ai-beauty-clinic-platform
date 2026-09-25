from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicalReportViewSet

router = DefaultRouter()
router.register(r'medical-reports', MedicalReportViewSet, basename='medical-report')

urlpatterns = [
    path('', include(router.urls)),
]
