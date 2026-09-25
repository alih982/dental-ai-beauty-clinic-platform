from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone

@login_required
def dashboard_home(request):
    user = request.user
    if user.is_doctor:
        return redirect('doctor_dashboard')
    elif user.is_patient:
        return redirect('patient_dashboard')
    else:
        return redirect('patient_dashboard') # Default fallback

@method_decorator(login_required, name='dispatch')
class PatientDashboardView(View):
    def get(self, request):
        return render(request, 'patient-dashboard.html', {'user': request.user})

@method_decorator(login_required, name='dispatch')
class DoctorDashboardView(View):
    def get(self, request):
        return render(request, 'doctor-profile.html', {'user': request.user})


# ====================
# Admin Stats API
# ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    """
    Get admin dashboard statistics.
    """
    from apps.accounts.models import User
    from apps.appointments.domain.models import Appointment
    from apps.doctors.models import Doctor
    from apps.patients.models import Patient
    
    # Get counts
    total_users = User.objects.count()
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    
    # Get today's date range
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Active appointments (today)
    active_appointments = Appointment.objects.filter(
        appointment_date__gte=today,
        appointment_date__lt=tomorrow,
        status__in=['confirmed', 'pending']
    ).count()
    
    # Calculate system health (mock for now - can be extended)
    system_health = 98
    
    return Response({
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'active_appointments': active_appointments,
        'system_health': system_health,
    })


# ====================
# Doctor Stats API
# ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_stats(request):
    """
    Get doctor dashboard statistics.
    """
    from apps.appointments.domain.models import Appointment
    from apps.doctors.models import Doctor
    
    # Get doctor from user
    doctor = None
    if hasattr(request.user, 'doctor_profile'):
        doctor = request.user.doctor_profile
    else:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=404
            )
    
    # Get today's date range
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Total unique patients
    total_patients = Appointment.objects.filter(
        doctor=doctor
    ).values('patient').distinct().count()
    
    # Upcoming appointments (today)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=today,
        appointment_date__lt=tomorrow,
        status__in=['confirmed', 'pending']
    ).count()
    
    # Completed consultations (all time)
    completed_consultations = Appointment.objects.filter(
        doctor=doctor,
        status='completed'
    ).count()
    
    # Rating
    rating = float(doctor.rating) if doctor.rating else 0.0
    
    return Response({
        'total_patients': total_patients,
        'upcoming_appointments': upcoming_appointments,
        'completed_consultations': completed_consultations,
        'rating': rating,
    })
