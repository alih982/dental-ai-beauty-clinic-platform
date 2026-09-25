"""Patient domain services - Business logic"""
from typing import Dict, Any, List
from datetime import date
import logging

from apps.core.services import BaseService
from apps.patients.infrastructure.repositories import PatientRepository
from apps.patients.domain.models import Patient, MedicalHistory, Allergy, Medication


logger = logging.getLogger('apps.patients')


class PatientService(BaseService[Patient]):
    """Patient business logic service"""
    
    def __init__(self):
        super().__init__(PatientRepository())
    
    async def get_patient_with_medical_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient with all medical information.
        
        Returns complete patient profile including:
        - Basic info
        - Medical history
        - Allergies
        - Current medications
        """
        patient = await self.repository.aget_by_id(patient_id)
        if not patient:
            return None
        
        # Get related medical data
        medical_history = await MedicalHistory.objects.filter(
            patient_id=patient_id,
            is_active=True
        ).alist()
        
        allergies = await Allergy.objects.filter(
            patient_id=patient_id
        ).alist()
        
        medications = await Medication.objects.filter(
            patient_id=patient_id,
            is_active=True
        ).alist()
        
        return {
            'patient': patient,
            'age': patient.age,
            'medical_history': list(medical_history),
            'allergies': list(allergies),
            'medications': list(medications),
        }
    
    async def add_medical_history(
        self,
        patient_id: str,
        condition: str,
        diagnosis_date: date,
        treatment: str = None,
        notes: str = None
    ) -> MedicalHistory:
        """Add medical history record"""
        history = await MedicalHistory.objects.acreate(
            patient_id=patient_id,
            condition=condition,
            diagnosis_date=diagnosis_date,
            treatment=treatment or '',
            notes=notes or ''
        )
        
        logger.info(f"Medical history added for patient {patient_id}: {condition}")
        return history
    
    async def add_allergy(
        self,
        patient_id: str,
        allergen: str,
        reaction: str,
        severity: str = 'mild',
        notes: str = None
    ) -> Allergy:
        """Add allergy record"""
        allergy = await Allergy.objects.acreate(
            patient_id=patient_id,
            allergen=allergen,
            reaction=reaction,
            severity=severity,
            notes=notes or ''
        )
        
        logger.info(f"Allergy added for patient {patient_id}: {allergen}")
        return allergy
    
    async def get_patient_appointments(self, patient_id: str) -> List[Any]:
        """Get patient's appointment history"""
        from apps.appointments.domain.models import Appointment
        
        appointments = await Appointment.objects.filter(
            patient_id=patient_id
        ).select_related('doctor').order_by('-appointment_date').alist()
        
        return list(appointments)
