from django.core.management.base import BaseCommand
from django.db import transaction
from apps.doctors.domain.models import Doctor, Specialty
from apps.accounts.models import User
import random

class Command(BaseCommand):
    help = 'Seed doctors data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding doctors data...')

        # Create specialties if they don't exist
        specialties_data = [
            {'name_fa': 'داخلی', 'name_en': 'Internal Medicine', 'description': 'Internal Medicine'},
            {'name_fa': 'قلب و عروق', 'name_en': 'Cardiology', 'description': 'Cardiology'},
            {'name_fa': 'مغز و اعصاب', 'name_en': 'Neurology', 'description': 'Neurology'},
            {'name_fa': 'ارتوپدی', 'name_en': 'Orthopedics', 'description': 'Orthopedics'},
            {'name_fa': 'چشم پزشکی', 'name_en': 'Ophthalmology', 'description': 'Ophthalmology'},
            {'name_fa': 'دندانپزشکی', 'name_en': 'Dentistry', 'description': 'Dentistry'},
            {'name_fa': 'پوست و مو', 'name_en': 'Dermatology', 'description': 'Dermatology'},
            {'name_fa': 'زنان و زایمان', 'name_en': 'Obstetrics and Gynecology', 'description': 'Obstetrics and Gynecology'},
        ]

        specialties = []
        for specialty_data in specialties_data:
            specialty, created = Specialty.objects.get_or_create(
                name_en=specialty_data['name_en'],
                defaults=specialty_data
            )
            specialties.append(specialty)
            if created:
                self.stdout.write(f'Created specialty: {specialty.name_fa}')

        # Create doctors
        doctors_data = [
            {
                'first_name_fa': 'احمد',
                'last_name_fa': 'رضایی',
                'first_name_en': 'Ahmad',
                'last_name_en': 'Rezaei',
                'specialty': specialties[0],  # Internal Medicine
                'bio_fa': 'متخصص داخلی با بیش از 15 سال تجربه',
                'bio_en': 'Internal medicine specialist with over 15 years of experience',
                'fee': 150000,
                'years_of_experience': 15,
                'rating': 4.8,
                'review_count': 120,
                'clinic_name_fa': 'کلینیک تخصصی داخلی',
                'clinic_name_en': 'Internal Medicine Clinic',
                'city_fa': 'تهران',
                'city_en': 'Tehran',
                'is_active': True,
                'is_verified': True,
            },
            {
                'first_name_fa': 'مریم',
                'last_name_fa': 'احمدی',
                'first_name_en': 'Maryam',
                'last_name_en': 'Ahmadi',
                'specialty': specialties[1],  # Cardiology
                'bio_fa': 'متخصص قلب و عروق، فوق تخصص آنژیوگرافی',
                'bio_en': 'Cardiologist, subspecialist in angiography',
                'fee': 200000,
                'years_of_experience': 12,
                'rating': 4.9,
                'review_count': 95,
                'clinic_name_fa': 'مرکز قلب تهران',
                'clinic_name_en': 'Tehran Heart Center',
                'city_fa': 'تهران',
                'city_en': 'Tehran',
                'is_active': True,
                'is_verified': True,
            },
            {
                'first_name_fa': 'علی',
                'last_name_fa': 'محمدی',
                'first_name_en': 'Ali',
                'last_name_en': 'Mohammadi',
                'specialty': specialties[2],  # Neurology
                'bio_fa': 'متخصص مغز و اعصاب، درمان سردردهای مزمن',
                'bio_en': 'Neurologist, specialist in chronic headache treatment',
                'fee': 180000,
                'years_of_experience': 10,
                'rating': 4.7,
                'review_count': 85,
                'clinic_name_fa': 'کلینیک مغز و اعصاب',
                'clinic_name_en': 'Neurology Clinic',
                'city_fa': 'اصفهان',
                'city_en': 'Isfahan',
                'is_active': True,
                'is_verified': True,
            },
            {
                'first_name_fa': 'فاطمه',
                'last_name_fa': 'حسینی',
                'first_name_en': 'Fateme',
                'last_name_en': 'Hosseini',
                'specialty': specialties[3],  # Orthopedics
                'bio_fa': 'متخصص ارتوپدی، جراحی مفاصل',
                'bio_en': 'Orthopedic specialist, joint surgery',
                'fee': 220000,
                'years_of_experience': 14,
                'rating': 4.6,
                'review_count': 110,
                'clinic_name_fa': 'مرکز ارتوپدی اصفهان',
                'clinic_name_en': 'Isfahan Orthopedic Center',
                'city_fa': 'اصفهان',
                'city_en': 'Isfahan',
                'is_active': True,
                'is_verified': True,
            },
            {
                'first_name_fa': 'حسن',
                'last_name_fa': 'کریمی',
                'first_name_en': 'Hassan',
                'last_name_en': 'Karimi',
                'specialty': specialties[4],  # Ophthalmology
                'bio_fa': 'متخصص چشم، جراحی آب مروارید',
                'bio_en': 'Ophthalmologist, cataract surgery',
                'fee': 160000,
                'years_of_experience': 8,
                'rating': 4.8,
                'review_count': 75,
                'clinic_name_fa': 'کلینیک چشم پزشکی',
                'clinic_name_en': 'Ophthalmology Clinic',
                'city_fa': 'مشهد',
                'city_en': 'Mashhad',
                'is_active': True,
                'is_verified': True,
            },
        ]

        for doctor_data in doctors_data:
            # Create user for doctor
            username = f"{doctor_data['first_name_en'].lower()}.{doctor_data['last_name_en'].lower()}"
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@hospital.com",
                    'phone_number': f"0912{random.randint(1000000, 9999999)}",
                    'first_name': doctor_data['first_name_fa'],
                    'last_name': doctor_data['last_name_fa'],
                    'is_active': True,
                }
            )

            # Create doctor profile
            doctor, created = Doctor.objects.get_or_create(
                user=user,
                defaults=doctor_data
            )

            if created:
                self.stdout.write(f'Created doctor: {doctor.get_full_name_fa()}')
            else:
                # Update existing doctor
                for key, value in doctor_data.items():
                    setattr(doctor, key, value)
                doctor.save()
                self.stdout.write(f'Updated doctor: {doctor.get_full_name_fa()}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded doctors data'))
