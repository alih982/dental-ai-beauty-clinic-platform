"""Patient repositories"""
from apps.core.repositories import BaseRepository
from apps.patients.domain.models import Patient, MedicalHistory, Allergy, Medication


class PatientRepository(BaseRepository[Patient]):
    """Repository for Patient aggregate"""
    
    def __init__(self):
        super().__init__(Patient)


class MedicalHistoryRepository(BaseRepository[MedicalHistory]):
    """Repository for MedicalHistory"""
    
    def __init__(self):
        super().__init__(MedicalHistory)


class AllergyRepository(BaseRepository[Allergy]):
    """Repository for Allergy"""
    
    def __init__(self):
        super().__init__(Allergy)


class MedicationRepository(BaseRepository[Medication]):
    """Repository for Medication"""
    
    def __init__(self):
        super().__init__(Medication)
