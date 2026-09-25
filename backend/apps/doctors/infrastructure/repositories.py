"""Doctor repositories"""
from apps.core.repositories import BaseRepository
from apps.doctors.domain.models import Doctor, Specialty, DoctorWorkingHours


class DoctorRepository(BaseRepository[Doctor]):
    """Repository for Doctor aggregate"""
    
    def __init__(self):
        super().__init__(Doctor)
    
    def get_queryset(self):
        """Optimize queries with select_related"""
        return super().get_queryset().select_related('specialty')


class SpecialtyRepository(BaseRepository[Specialty]):
    """Repository for Specialty entity"""
    
    def __init__(self):
        super().__init__(Specialty)


class DoctorWorkingHoursRepository(BaseRepository[DoctorWorkingHours]):
    """Repository for DoctorWorkingHours"""
    
    def __init__(self):
        super().__init__(DoctorWorkingHours)
