from django.urls import path
from .views import (
    dashboard_home,
    PatientDashboardView,
    DoctorDashboardView,
    admin_stats,
    doctor_stats
)

urlpatterns = [
    path('', dashboard_home, name='dashboard_home'),
    path('home/', dashboard_home, name='home'),
    path('patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('doctor/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    
    # API Endpoints - simplified paths
    path('admin/stats/', admin_stats, name='admin_stats'),
    path('doctor/stats/', doctor_stats, name='doctor_stats'),
]
