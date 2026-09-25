import os
import django

import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.cms.models import LandingPageHeader, MedicalService, PatientReview, AboutSection

def populate():
    # 1. Landing Page Header
    LandingPageHeader.objects.get_or_create(
        is_active=True,
        defaults={
            'title': '<b>Professional</b> Medical Services You Can Trust',
            'subtitle': 'Experience world-class healthcare with DoctorHub. From expert diagnosis to advanced treatments, we are here for you.',
            'search_placeholder': 'Search Doctors, Clinics, Specialties...',
            'active_doctors_count': '2k+',
            'user_rating': '4.9/5'
        }
    )

    # 2. About Section
    AboutSection.objects.get_or_create(
        is_active=True,
        defaults={
            'tag': 'ABOUT OUR HOSPITAL',
            'title': 'Experience <b>Excellence</b> in Modern Healthcare',
            'paragraph_1': 'DoctorHub is a leading healthcare provider dedicated to providing exceptional medical care and services. Our team of expert doctors and state-of-the-art facilities ensure you receive the best possible treatment.',
            'paragraph_2': 'We believe in a patient-centered approach, combining cutting-edge technology with compassionate care to improve lives across the globe.',
            'feature_1': 'Expert Doctors',
            'feature_2': '24/7 Support',
            'feature_3': 'Modern Equipment'
        }
    )

    # 3. Medical Services
    MedicalService.objects.all().delete()
    services = [
        {
            'title_en': 'Cardiology', 
            'title_fa': 'قلب و عروق',
            'slug': 'cardiology',
            'description_en': 'Comprehensive heart care and diagnosis.', 
            'description_fa': 'مراقبت‌های جامع قلبی و تشخیص بیماری‌های عروق.',
            'content_en': 'Our cardiology department is equipped with the latest technology for heart surgery, rhythm management, and non-invasive diagnostics.',
            'content_fa': 'بخش قلب ما مجهز به آخرین فناوری‌ها برای جراحی قلب، مدیریت ریتم و تشخیص‌های غیرتهاجمی است.',
            'icon_name': 'Heart', 
            'color_class': 'bg-red-50 text-red-600', 
            'order': 1
        },
        {
            'title_en': 'Eye Care', 
            'title_fa': 'چشم پزشکی',
            'slug': 'eye-care',
            'description_en': 'Professional vision testing and eye health.', 
            'description_fa': 'تست بینایی حرفه‌ای و سلامت چشم.',
            'content_en': 'Expert ophthalmologists providing laser surgery, cataract treatment, and routine vision care.',
            'content_fa': 'متخصصان چشم‌پزشک جراحی لیزر، درمان آب مروارید و مراقبت‌های روتین بینایی را ارائه می‌دهند.',
            'icon_name': 'Eye', 
            'color_class': 'bg-blue-50 text-blue-600', 
            'order': 2
        },
        {
            'title_en': 'Neurology', 
            'title_fa': 'مغز و اعصاب',
            'slug': 'neurology',
            'description_en': 'Expert care for brain and nervous system.', 
            'description_fa': 'مراقبت‌های تخصصی برای مغز و سیستم عصبی.',
            'content_en': 'Advanced neuro-diagnostics and treatment for complex neurological conditions.',
            'content_fa': 'تشخیص‌های پیشرفته عصبی و درمان شرایط پیچیده مغز و اعصاب.',
            'icon_name': 'Brain', 
            'color_class': 'bg-purple-50 text-purple-600', 
            'order': 3
        },
        {
            'title_en': 'Surgical', 
            'title_fa': 'جراحی',
            'slug': 'surgical',
            'description_en': 'Advanced surgical procedures with precision.', 
            'description_fa': 'روش‌های جراحی پیشرفته با دقت بالا.',
            'content_en': 'State-of-the-art operating theaters and expert surgical teams in various disciplines.',
            'content_fa': 'اتاق‌های عمل پیشرفته و تیم‌های جراحی متخصص در رشته‌های مختلف.',
            'icon_name': 'Activity', 
            'color_class': 'bg-indigo-50 text-indigo-600', 
            'order': 4
        },
    ]

    for svc in services:
        MedicalService.objects.create(**svc)

    # 4. Patient Reviews
    reviews = [
        {
            'patient_name': 'Thomas Isral',
            'patient_role': 'Patient',
            'review_text': "The software has provided more insight for computer designers, especially those specialized in medical interfaces. It's a game changer.",
            'image_url': 'http://i.pravatar.cc/150?u=1'
        },
        {
            'patient_name': 'Carl Oliver',
            'patient_role': 'Consultant',
            'review_text': 'I was impressed by the speed and accuracy of the AI diagnosis tools. The medical team is also very professional.',
            'image_url': 'http://i.pravatar.cc/150?u=2'
        },
        {
            'patient_name': 'Barbara Mink',
            'patient_role': 'Doctor',
            'review_text': 'Managing my schedule and patients has never been easier. The platform is intuitive and covers all my needs.',
            'image_url': 'http://i.pravatar.cc/150?u=3'
        }
    ]

    for rev in reviews:
        PatientReview.objects.get_or_create(
            patient_name=rev['patient_name'],
            defaults={
                'patient_role': rev['patient_role'],
                'review_text': rev['review_text'],
                'image_url': rev['image_url']
            }
        )

    # 5. Navigation Menu
    from apps.cms.models import NavMenuItem
    NavMenuItem.objects.all().delete()
    
    # Root items
    home = NavMenuItem.objects.create(label_en='Home', label_fa='خانه', url='/', order=1)
    services = NavMenuItem.objects.create(label_en='Services', label_fa='خدمات', url='/services', order=2, is_mega_menu=True)
    doctors = NavMenuItem.objects.create(label_en='Doctors', label_fa='پزشکان', url='/doctors', order=3)
    about = NavMenuItem.objects.create(label_en='About', label_fa='درباره ما', url='/about', order=4)
    contact = NavMenuItem.objects.create(label_en='Contact', label_fa='تماس', url='/contact', order=5)
    
    # Sub-items for Services (Mega Menu simulation)
    NavMenuItem.objects.create(label_en='Cardiology', label_fa='قلب و عروق', url='/services/cardiology', parent=services, order=1, icon_name='Heart')
    NavMenuItem.objects.create(label_en='Neurology', label_fa='مغز و اعصاب', url='/services/neurology', parent=services, order=2, icon_name='Brain')
    NavMenuItem.objects.create(label_en='Surgical', label_fa='جراحی', url='/services/surgical', parent=services, order=3, icon_name='Activity')
    NavMenuItem.objects.create(label_en='Eye Care', label_fa='چشم پزشکی', url='/services/eye-care', parent=services, order=4, icon_name='Eye')

    print("CMS Data Sample Populated Successfully!")

if __name__ == '__main__':
    populate()
