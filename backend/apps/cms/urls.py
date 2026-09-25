from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CMSContentViewSet, MedicalServiceViewSet, PatientReviewViewSet, NavMenuItemViewSet

router = DefaultRouter()
router.register(r'content', CMSContentViewSet, basename='cms-content')
router.register(r'services', MedicalServiceViewSet)
router.register(r'reviews', PatientReviewViewSet)
router.register(r'menu', NavMenuItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
