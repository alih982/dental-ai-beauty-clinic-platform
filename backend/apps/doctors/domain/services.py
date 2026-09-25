"""Doctor domain services - Business logic"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from django.db.models import Q, Count, Avg
import logging

from apps.core.services import BaseService
from apps.doctors.infrastructure.repositories import DoctorRepository, SpecialtyRepository
from apps.doctors.domain.models import Doctor, Specialty


logger = logging.getLogger('apps.doctors')


class DoctorService(BaseService[Doctor]):
    """Doctor business logic service"""
    
    def __init__(self):
        super().__init__(DoctorRepository())
        self.specialty_repo = SpecialtyRepository()
    
    async def search_doctors(
        self,
        query: str = None,
        specialty_id: str = None,
        city: str = None,
        min_rating: Decimal = None,
        max_fee: Decimal = None,
        accepts_insurance: bool = None,
        limit: int = 20
    ) -> List[Doctor]:
        """
        Advanced doctor search with filters.
        
        Args:
            query: Search in doctor name, bio
            specialty_id: Filter by specialty
            city: Filter by city
            min_rating: Minimum rating
            max_fee: Maximum consultation fee
            accepts_insurance: Insurance acceptance
            limit: Results limit
        """
        filters = Q(is_active=True, is_verified=True)
        
        if query:
            filters &= (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(bio__icontains=query)
            )
        
        if specialty_id:
            filters &= Q(specialty_id=specialty_id)
        
        if city:
            filters &= Q(city__iexact=city)
        
        if min_rating:
            filters &= Q(rating__gte=min_rating)
        
        if max_fee:
            filters &= Q(fee__lte=max_fee)
        
        if accepts_insurance is not None:
            filters &= Q(accepts_insurance=accepts_insurance)
        
        doctors = await self.repository.afilter(filters, limit=limit)
        
        logger.info(f"Doctor search: {len(doctors)} results")
        return doctors
    
    async def get_top_rated_doctors(self, specialty_id: str = None, limit: int = 10) -> List[Doctor]:
        """Get top rated doctors"""
        filters = Q(is_active=True, is_verified=True, review_count__gte=5)
        
        if specialty_id:
            filters &= Q(specialty_id=specialty_id)
        
        return await self.repository.afilter(
            filters,
            order_by=['-rating', '-review_count'],
            limit=limit
        )
    
    async def get_doctor_statistics(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor statistics"""
        doctor = await self.repository.aget_by_id(doctor_id)
        if not doctor:
            return {}
        
        from apps.appointments.domain.models import Appointment
        
        # Get appointment stats
        total_appointments = await Appointment.objects.filter(
            doctor_id=doctor_id
        ).acount()
        
        completed_appointments = await Appointment.objects.filter(
            doctor_id=doctor_id,
            status=Appointment.Status.COMPLETED
        ).acount()
        
        return {
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'rating': float(doctor.rating),
            'review_count': doctor.review_count,
            'patient_count': doctor.patient_count,
            'years_of_experience': doctor.years_of_experience,
        }


class SpecialtyService(BaseService[Specialty]):
    """Specialty business logic service"""
    
    def __init__(self):
        super().__init__(SpecialtyRepository())
    
    async def get_popular_specialties(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular specialties with doctor count"""
        specialties = await Specialty.objects.annotate(
            doctor_count=Count('doctors', filter=Q(doctors__is_active=True))
        ).filter(doctor_count__gt=0).order_by('-doctor_count')[:limit].alist()
        
        return [
            {
                'id': str(s.id),
                'name': s.name,
                'name_en': s.name_en,
                'doctor_count': s.doctor_count,
                'icon': s.icon
            }
            for s in specialties
        ]
