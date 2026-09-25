from rest_framework import viewsets, permissions
from .models import MedicalReport
from .serializers import MedicalReportSerializer

class MedicalReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient_profile'):
            return MedicalReport.objects.filter(patient=user.patient_profile)
        elif hasattr(user, 'doctor_profile'):
            return MedicalReport.objects.filter(doctor=user.doctor_profile)
        return MedicalReport.objects.none()
