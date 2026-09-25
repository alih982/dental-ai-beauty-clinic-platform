"""
Management command to seed CMS data
"""
from django.core.management.base import BaseCommand
from apps.cms.models import MedicalService, PatientReview, AboutSection, LandingPageHeader, NavMenuItem


class Command(BaseCommand):
    help = 'Seed CMS data for the application'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CMS data...')
        
        # Create Landing Page Header
        header, created = LandingPageHeader.objects.get_or_create(
            defaults={
                'title': '<b>Professional</b> Medical Services You Can Trust',
                'subtitle': 'Experience world-class healthcare with DoctorHub. From expert diagnosis to advanced treatments, we are here for you.',
                'search_placeholder': 'Search Doctors, Clinics, Specialties...',
                'active_doctors_count': '500+',
                'user_rating': '4.9/5',
                'is_active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Landing header {"created" if created else "already exists"}'))

        # Create Medical Services
        services_data = [
            {
                'title_en': 'Cardiology',
                'title_fa': 'قلب و عروق',
                'slug': 'cardiology',
                'description_en': 'Heart and cardiovascular care',
                'description_fa': 'مراقبت از قلب و عروق',
                'content_en': 'Our cardiology department provides comprehensive heart care services including diagnostic testing, interventional procedures, and preventive cardiology.',
                'content_fa': 'بخش قلب و عروق ما خدمات جامع مراقبت از قلب including diagnostic testing, interventional procedures, and preventive cardiology را ارائه می دهد.',
                'icon_name': 'Heart',
                'color_class': 'bg-red-50 text-red-600',
                'order': 1,
            },
            {
                'title_en': 'Neurology',
                'title_fa': 'مغز و اعصاب',
                'slug': 'neurology',
                'description_en': 'Brain and nervous system care',
                'description_fa': 'مراقبت از مغز و سیستم عصبی',
                'content_en': 'Our neurology department offers advanced treatment for neurological disorders including stroke, epilepsy, and movement disorders.',
                'content_fa': 'بخش مغز و اعصاب ما درمان پیشرفته برای اختلالات عصبی از جمله سکته مغزی، صرع و اختلالات حرکتی را ارائه می دهد.',
                'icon_name': 'Brain',
                'color_class': 'bg-purple-50 text-purple-600',
                'order': 2,
            },
            {
                'title_en': 'Orthopedics',
                'title_fa': 'ارتوپدی',
                'slug': 'orthopedics',
                'description_en': 'Bone and joint care',
                'description_fa': 'مراقبت از استخوان و مفاصل',
                'content_en': 'Comprehensive orthopedic care for bone and joint conditions, sports injuries, and rehabilitation services.',
                'content_fa': 'مراقبت جامع ارتوپدی برای شرایط استخوان و مفاصل، آسیب های ورزشی و خدمات توانبخشی.',
                'icon_name': 'Bone',
                'color_class': 'bg-amber-50 text-amber-600',
                'order': 3,
            },
            {
                'title_en': 'Pediatrics',
                'title_fa': 'کودکان',
                'slug': 'pediatrics',
                'description_en': 'Child healthcare services',
                'description_fa': 'خدمات بهداشتی کودکان',
                'content_en': 'Complete pediatric care from newborn to adolescent, including preventive care, vaccinations, and treatment of childhood illnesses.',
                'content_fa': 'مراقبت کامل pediatric از نوزاد تا نوجوان، از جمله مراقبت های پیشگیرانه، واکسیناسیون و درمان بیماری های دوران کودکی.',
                'icon_name': 'Baby',
                'color_class': 'bg-pink-50 text-pink-600',
                'order': 4,
            },
            {
                'title_en': 'Dermatology',
                'title_fa': 'پوست و مو',
                'slug': 'dermatology',
                'description_en': 'Skin and hair care',
                'description_fa': 'مراقبت از پوست و مو',
                'content_en': 'Expert dermatological services for skin conditions, cosmetic procedures, and hair restoration.',
                'content_fa': 'خدمات تخصصی پوستی برای شرایط پوست، روش های آرایشی و بازسازی مو.',
                'icon_name': 'Sparkles',
                'color_class': 'bg-orange-50 text-orange-600',
                'order': 5,
            },
            {
                'title_en': 'Ophthalmology',
                'title_fa': 'چشم پزشکی',
                'slug': 'ophthalmology',
                'description_en': 'Eye care services',
                'description_fa': 'خدمات مراقبت از چشم',
                'content_en': 'Comprehensive eye care including cataract surgery, laser vision correction, and treatment of eye diseases.',
                'content_fa': 'مراقبت جامع از چشم از جمله جراحی آب مروارید، اصلاح بینایی لیزری و درمان بیماری های چشم.',
                'icon_name': 'Eye',
                'color_class': 'bg-blue-50 text-blue-600',
                'order': 6,
            },
        ]

        for service_data in services_data:
            service, created = MedicalService.objects.get_or_create(
                slug=service_data['slug'],
                defaults=service_data
            )
            self.stdout.write(self.style.SUCCESS(f'Service {service.title_en} {"created" if created else "already exists"}'))

        # Create About Section
        about, created = AboutSection.objects.get_or_create(
            defaults={
                'tag': 'ABOUT OUR HOSPITAL',
                'title': 'Experience <b>Excellence</b> in Modern Healthcare',
                'paragraph_1': 'We are dedicated to providing exceptional healthcare services with a focus on patient-centered care. Our team of experienced professionals uses state-of-the-art technology to deliver the best possible outcomes.',
                'paragraph_2': 'With facilities across the region, we strive to make quality healthcare accessible to everyone.',
                'feature_1': 'Expert Doctors',
                'feature_2': '24/7 Support',
                'feature_3': 'Modern Equipment',
                'is_active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'About section {"created" if created else "already exists"}'))

        # Create Patient Reviews
        reviews_data = [
            {
                'patient_name': 'Sarah Johnson',
                'patient_role': 'Cardiology Patient',
                'review_text': 'Excellent care and professional staff. The doctors explained everything clearly and made me feel comfortable throughout my treatment.',
                'rating': 5.0,
                'image_url': 'http://i.pravatar.cc/150?img=1',
            },
            {
                'patient_name': 'Mohammad Rezaei',
                'patient_role': 'Neurology Patient',
                'review_text': 'Very satisfied with the treatment. The neurology team was knowledgeable and compassionate.',
                'rating': 5.0,
                'image_url': 'http://i.pravatar.cc/150?img=3',
            },
            {
                'patient_name': 'Emily Davis',
                'patient_role': 'Pediatrics Parent',
                'review_text': 'Best pediatric care in the region. The staff is wonderful with children.',
                'rating': 4.9,
                'image_url': 'http://i.pravatar.cc/150?img=5',
            },
        ]

        for review_data in reviews_data:
            review, created = PatientReview.objects.get_or_create(
                patient_name=review_data['patient_name'],
                defaults={**review_data, 'is_active': True}
            )
            self.stdout.write(self.style.SUCCESS(f'Review by {review.patient_name} {"created" if created else "already exists"}'))

        # Create Nav Menu Items with proper hierarchy and mega menu
        # First, clear existing menu items to avoid duplicates
        NavMenuItem.objects.all().delete()
        
        # Create main menu items
        home_menu = NavMenuItem.objects.create(
            label_en='Home',
            label_fa='خانه',
            url='/',
            order=1,
            icon_name='Home',
            is_active=True,
            is_mega_menu=False
        )
        
        doctors_menu = NavMenuItem.objects.create(
            label_en='Doctors',
            label_fa='پزشکان',
            url='/doctors',
            order=2,
            icon_name='Stethoscope',
            is_active=True,
            is_mega_menu=False
        )
        
        # Services menu with mega menu
        services_menu = NavMenuItem.objects.create(
            label_en='Services',
            label_fa='خدمات',
            url='/services',
            order=3,
            icon_name='Activity',
            is_active=True,
            is_mega_menu=True
        )
        
        # Create child menu items for Services (mega menu items)
        service_children = [
            {'label_en': 'Cardiology', 'label_fa': 'قلب و عروق', 'slug': 'cardiology', 'icon': 'Heart'},
            {'label_en': 'Neurology', 'label_fa': 'مغز و اعصاب', 'slug': 'neurology', 'icon': 'Brain'},
            {'label_en': 'Orthopedics', 'label_fa': 'ارتوپدی', 'slug': 'orthopedics', 'icon': 'Bone'},
            {'label_en': 'Pediatrics', 'label_fa': 'کودکان', 'slug': 'pediatrics', 'icon': 'Baby'},
            {'label_en': 'Dermatology', 'label_fa': 'پوست و مو', 'slug': 'dermatology', 'icon': 'Sparkles'},
            {'label_en': 'Ophthalmology', 'label_fa': 'چشم پزشکی', 'slug': 'ophthalmology', 'icon': 'Eye'},
        ]
        
        for idx, svc in enumerate(service_children, 1):
            NavMenuItem.objects.create(
                label_en=svc['label_en'],
                label_fa=svc['label_fa'],
                url=f'/services/{svc["slug"]}',
                parent=services_menu,
                order=idx,
                icon_name=svc['icon'],
                is_active=True,
                is_mega_menu=False
            )
        
        pharmacy_menu = NavMenuItem.objects.create(
            label_en='Pharmacy',
            label_fa='داروخانه',
            url='/pharmacy',
            order=4,
            icon_name='Pill',
            is_active=True,
            is_mega_menu=False
        )
        
        about_menu = NavMenuItem.objects.create(
            label_en='About',
            label_fa='درباره ما',
            url='/about',
            order=5,
            icon_name='Users',
            is_active=True,
            is_mega_menu=False
        )
        
        contact_menu = NavMenuItem.objects.create(
            label_en='Contact',
            label_fa='تماس',
            url='/contact',
            order=6,
            icon_name='Phone',
            is_active=True,
            is_mega_menu=False
        )

        for menu_data in [home_menu, doctors_menu, services_menu, pharmacy_menu, about_menu, contact_menu]:
            self.stdout.write(self.style.SUCCESS(f'Menu item {menu_data.label_en} {"created" if menu_data else "already exists"}'))

        self.stdout.write(self.style.SUCCESS('CMS data seeding completed!'))
        self.stdout.write('')
        self.stdout.write('Now you can access:')
        self.stdout.write('  - /services - List of medical services')
        self.stdout.write('  - /services/cardiology - Service detail page')
        self.stdout.write('  - Home page with services and reviews')

