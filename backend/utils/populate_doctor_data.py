import os
import sys
import django
import uuid
from decimal import Decimal

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django
django.setup()

from apps.doctors.domain.models import Doctor, Specialty, DoctorWorkingHours

def populate_doctors():
    print("Populating Doctor and Specialty data...")

    # Clear existing data
    DoctorWorkingHours.objects.all().delete()
    Doctor.objects.all().delete()
    Specialty.objects.all().delete()

    # 1. Create Specialties
    specialties_data = [
        {
            "name_fa": "قلب و عروق",
            "name_en": "Cardiology",
            "description_fa": "متخصص در بیماری‌های قلب و سیستم گردش خون",
            "description_en": "Specialized in diseases of the heart and circulatory system",
            "icon": "Heart"
        },
        {
            "name_fa": "مغز و اعصاب",
            "name_en": "Neurology",
            "description_fa": "متخصص در اختلالات سیستم عصبی",
            "description_en": "Specialized in disorders of the nervous system",
            "icon": "Brain"
        },
        {
            "name_fa": "کودکان",
            "name_en": "Pediatrics",
            "description_fa": "مراقبت‌های پزشکی برای نوزادان، کودکان و نوجوانان",
            "description_en": "Medical care for infants, children, and adolescents",
            "icon": "Baby"
        },
        {
            "name_fa": "پوست و مو",
            "name_en": "Dermatology",
            "description_fa": "متخصص در بیماری‌های پوست، مو و ناخن",
            "description_en": "Specialized in diseases of skin, hair, and nails",
            "icon": "Sparkles"
        },
        {
            "name_fa": "ارتوپدی",
            "name_en": "Orthopedics",
            "description_fa": "متخصص در سیستم اسکلتی عضلانی",
            "description_en": "Specialized in the musculoskeletal system",
            "icon": "Bones"
        }
    ]

    specialties = {}
    for data in specialties_data:
        spec = Specialty.objects.create(**data)
        specialties[data['name_en']] = spec
        print(f"Created Specialty: {data['name_en']}")

    # 2. Create Doctors
    doctors_data = [
        {
            "first_name_fa": "سارا",
            "first_name_en": "Sarah",
            "last_name_fa": "اسمیت",
            "last_name_en": "Smith",
            "national_code": "1234567890",
            "phone": "09123456789",
            "email": "sarah.smith@DoctorHub.com",
            "medical_council_number": "MC12345",
            "specialty": specialties["Cardiology"],
            "sub_specialty_fa": "فلوشیپ اینترونشنال کاردیولوژی",
            "sub_specialty_en": "Interventional Cardiology Fellowship",
            "years_of_experience": 15,
            "education_fa": "دکترای حرفه‌ای پزشکی از دانشگاه تهران، تخصص قلب از دانشگاه برلین",
            "education_en": "MD from Tehran University, Cardiology Residency from Berlin University",
            "clinic_name_fa": "مرکز قلب تهران",
            "clinic_name_en": "Tehran Heart Center",
            "clinic_address_fa": "تهران، خیابان ولیعصر، نرسیده به میدان ونک",
            "clinic_address_en": "Valiasr St, near Vanak Sq, Tehran",
            "city_fa": "تهران",
            "city_en": "Tehran",
            "fee": Decimal("150000"),
            "accepts_insurance": True,
            "bio_fa": "دکتر سارا اسمیت متخصص برجسته قلب و عروق با بیش از ۱۵ سال تجربه در درمان بیماری‌های پیچیده قلبی.",
            "bio_en": "Dr. Sarah Smith is a prominent cardiologist with over 15 years of experience in treating complex heart diseases.",
            "is_verified": True,
            "rating": Decimal("4.9"),
            "review_count": 127
        },
        {
            "first_name_fa": "مایک",
            "first_name_en": "Mike",
            "last_name_fa": "جانسون",
            "last_name_en": "Johnson",
            "national_code": "0987654321",
            "phone": "09987654321",
            "email": "mike.j@DoctorHub.com",
            "medical_council_number": "MC54321",
            "specialty": specialties["Neurology"],
            "sub_specialty_fa": "متخصص بیماری‌های مغز و اعصاب",
            "sub_specialty_en": "Neurology Specialist",
            "years_of_experience": 12,
            "education_fa": "تخصص مغز و اعصاب از دانشگاه آکسفورد",
            "education_en": "Neurology Residency from Oxford University",
            "clinic_name_fa": "کلینیک نورو پلاس",
            "clinic_name_en": "NeuroClinic Plus",
            "clinic_address_fa": "تهران، شریعتی، بالاتر از ظفر",
            "clinic_address_en": "Shariati St, Tehran",
            "city_fa": "تهران",
            "city_en": "Tehran",
            "fee": Decimal("140000"),
            "accepts_insurance": True,
            "bio_fa": "دکتر مایک جانسون متخصص مغز و اعصاب، متخصص در درمان میگرن و صرع.",
            "bio_en": "Dr. Mike Johnson is a neurologist specialized in migraine and epilepsy treatment.",
            "is_verified": True,
            "rating": Decimal("4.8"),
            "review_count": 94
        },
        {
            "first_name_fa": "احمد",
            "first_name_en": "Ahmad",
            "last_name_fa": "رضایی",
            "last_name_en": "Rezaei",
            "national_code": "1112223334",
            "phone": "09112223334",
            "email": "ahmad.r@DoctorHub.com",
            "medical_council_number": "MC11223",
            "specialty": specialties["Orthopedics"],
            "sub_specialty_fa": "جراح استخوان و مفاصل",
            "sub_specialty_en": "Orthopedic Surgeon",
            "years_of_experience": 18,
            "education_fa": "تخصص ارتوپدی از دانشگاه شهید بهشتی",
            "education_en": "Orthopedics from Shahid Beheshti University",
            "clinic_name_fa": "مرکز استخوان و مفاصل",
            "clinic_name_en": "Bone & Joint Center",
            "clinic_address_fa": "تهران، پاسداران، بوستان نهم",
            "clinic_address_en": "Pasداران St, Tehran",
            "city_fa": "تهران",
            "city_en": "Tehran",
            "fee": Decimal("160000"),
            "accepts_insurance": False,
            "bio_fa": "دکتر احمد رضایی جراح برجسته ارتوپد با سابقه طولانی در جراحی‌های زانو و لگن.",
            "bio_en": "Dr. Ahmad Rezaei is a leading orthopedic surgeon with a long history of knee and hip surgeries.",
            "is_verified": True,
            "rating": Decimal("4.7"),
            "review_count": 83
        }
    ]

    for data in doctors_data:
        doc = Doctor.objects.create(**data)
        print(f"Created Doctor: {data['first_name_en']} {data['last_name_en']}")
        
        # Add working hours
        for day in range(5): # Mon-Fri (or Sat-Wed in Iran context, but using IntegerChoices)
            DoctorWorkingHours.objects.create(
                doctor=doc,
                day_of_week=day,
                start_time="09:00:00",
                end_time="17:00:00"
            )

    print("Successfully populated Doctor data!")

if __name__ == "__main__":
    populate_doctors()
