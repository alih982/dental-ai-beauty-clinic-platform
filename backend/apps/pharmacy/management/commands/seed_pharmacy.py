from django.core.management.base import BaseCommand
from apps.pharmacy.domain.models import Category, Medicine
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seeds the database with initial Pharmacy data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Pharmacy data...')

        # 1. Categories - Using English names for compatibility with frontend
        categories_data = [
            {"name": "Heart Health", "slug": "heart-health", "icon": "❤️"},
            {"name": "Pain Relief", "slug": "pain-relief", "icon": "💊"},
            {"name": "Vitamins", "slug": "vitamins", "icon": "🌿"},
            {"name": "Cold & Flu", "slug": "cold-flu", "icon": "🤒"},
            {"name": "Skin Care", "slug": "skin-care", "icon": "✨"},
            {"name": "Diabetes", "slug": "diabetes", "icon": "🩸"},
            {"name": "Supplements", "slug": "supplements", "icon": "💪"},
            {"name": "Medical Equipment", "slug": "medical-equipment", "icon": "🌡️"},
            {"name": "Mother & Baby", "slug": "mother-baby", "icon": "🍼"},
            {"name": "First Aid", "slug": "first-aid", "icon": "🩹"},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'is_active': True
                }
            )
            categories[cat.slug] = cat
            if created:
                self.stdout.write(f'Created category: {cat.name}')

        # 2. Medicines
        medicines_data = [
            {
                "name": "Cardio Aspirin 100mg",
                "category": "heart-health",
                "price": 15000,
                "stock": 50,
                "pharmacy_name": "Central Pharmacy",
                "description": "Heart medication for cardiovascular health",
                "is_prescription_required": True,
            },
            {
                "name": "Vitamin D3 1000IU",
                "category": "vitamins",
                "price": 25000,
                "stock": 100,
                "pharmacy_name": "Health Store",
                "description": "Vitamin D supplement for bone health",
                "is_prescription_required": False,
            },
            {
                "name": "Ibuprofen 400mg",
                "category": "pain-relief",
                "price": 8000,
                "stock": 75,
                "pharmacy_name": "Central Pharmacy",
                "description": "Pain reliever and anti-inflammatory",
                "is_prescription_required": False,
            },
            {
                "name": "Omega-3 Fish Oil",
                "category": "heart-health",
                "price": 35000,
                "stock": 30,
                "pharmacy_name": "Natural Health",
                "description": "Heart health supplement rich in omega-3",
                "is_prescription_required": False,
            },
            {
                "name": "Vitamin C 1000mg",
                "category": "vitamins",
                "price": 18000,
                "stock": 200,
                "pharmacy_name": "Health Store",
                "description": "Immune system support supplement",
                "is_prescription_required": False,
            },
            {
                "name": "Cold Defense",
                "category": "cold-flu",
                "price": 22000,
                "stock": 45,
                "pharmacy_name": "Central Pharmacy",
                "description": "Cold and flu relief medication",
                "is_prescription_required": False,
            },
            {
                "name": "Moisturizing Cream",
                "category": "skin-care",
                "price": 28000,
                "stock": 60,
                "pharmacy_name": "Beauty Care",
                "description": "Deep moisturizing cream for dry skin",
                "is_prescription_required": False,
            },
            {
                "name": "Metformin 500mg",
                "category": "diabetes",
                "price": 12000,
                "stock": 25,
                "pharmacy_name": "Central Pharmacy",
                "description": "Diabetes medication for blood sugar control",
                "is_prescription_required": True,
            },
            {
                "name": "Blood Pressure Monitor",
                "category": "medical-equipment",
                "price": 450000,
                "stock": 10,
                "pharmacy_name": "Medical Supplies",
                "description": "Digital blood pressure monitor for home use",
                "is_prescription_required": False,
            },
            {
                "name": "Baby Formula Premium",
                "category": "mother-baby",
                "price": 180000,
                "stock": 40,
                "pharmacy_name": "BabyHealth",
                "description": "Nutritious infant formula for newborns",
                "is_prescription_required": False,
            },
            {
                "name": "First Aid Kit",
                "category": "first-aid",
                "price": 95000,
                "stock": 35,
                "pharmacy_name": "Emergency Supplies",
                "description": "Complete first aid kit for home and travel",
                "is_prescription_required": False,
            },
            {
                "name": "Multivitamin Complete",
                "category": "supplements",
                "price": 65000,
                "stock": 80,
                "pharmacy_name": "Health Store",
                "description": "Complete multivitamin for daily health",
                "is_prescription_required": False,
            },
            {
                "name": "Antibiotic Amoxicillin 500mg",
                "category": "pain-relief",
                "price": 15000,
                "stock": 0,  # Out of stock
                "pharmacy_name": "Central Pharmacy",
                "description": "Antibiotic for bacterial infections",
                "is_prescription_required": True,
            },
            {
                "name": "Allergy Relief",
                "category": "cold-flu",
                "price": 19500,
                "stock": 55,
                "pharmacy_name": "Central Pharmacy",
                "description": "Fast relief from seasonal allergies",
                "is_prescription_required": False,
            },
            {
                "name": "Insulin Glargine",
                "category": "diabetes",
                "price": 85000,
                "stock": 15,
                "pharmacy_name": "Central Pharmacy",
                "description": "Long-acting insulin for diabetes management",
                "is_prescription_required": True,
            },
        ]

        for item in medicines_data:
            cat_slug = item.pop('category')
            category = categories.get(cat_slug)
            
            if category:
                medicine, created = Medicine.objects.get_or_create(
                    slug=slugify(item['name']),
                    defaults={
                        'category': category,
                        **item,
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f"Created medicine: {item['name']}")
                else:
                    # Update existing medicine
                    for key, value in item.items():
                        setattr(medicine, key, value)
                    medicine.save()
                    self.stdout.write(f"Updated medicine: {item['name']}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded Pharmacy data'))
