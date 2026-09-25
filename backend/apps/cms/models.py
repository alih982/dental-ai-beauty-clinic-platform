from django.db import models

class LandingPageHeader(models.Model):
    title_en = models.CharField(max_length=255, default='<b>Professional</b> Medical Services You Can Trust')
    title_fa = models.CharField(max_length=255, default='<b>Professional</b> Medical Services You Can Trust')
    subtitle_en = models.TextField(default='Experience world-class healthcare with DoctorHub. From expert diagnosis to advanced treatments, we are here for you.')
    subtitle_fa = models.TextField(default='Experience world-class healthcare with DoctorHub. From expert diagnosis to advanced treatments, we are here for you.')
    search_placeholder_en = models.CharField(max_length=255, default='Search Doctors, Clinics, Specialties...')
    search_placeholder_fa = models.CharField(max_length=255, default='Search Doctors, Clinics, Specialties...')
    active_doctors_count = models.CharField(max_length=50, default='2k+')
    user_rating = models.CharField(max_length=50, default='4.9/5')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Landing Page Header'
        verbose_name_plural = 'Landing Page Headers'

    def __str__(self):
        return f"Header updated {self.updated_at}"

class MedicalService(models.Model):
    title_en = models.CharField(max_length=100)
    title_fa = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Unique URL identifier")
    description_en = models.TextField()
    description_fa = models.TextField()
    content_en = models.TextField(blank=True, help_text="Rich content for the service detail page")
    content_fa = models.TextField(blank=True, help_text="Rich content in Persian")
    icon_name = models.CharField(max_length=50, help_text='lucide icon name e.g. Heart')
    color_class = models.CharField(max_length=100, default='bg-blue-50 text-blue-600')
    featured_image = models.ImageField(upload_to='services/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title_en)
        super().save(*args, **kwargs)

class PatientReview(models.Model):
    patient_name_en = models.CharField(max_length=100)
    patient_name_fa = models.CharField(max_length=100, blank=True)
    patient_role_en = models.CharField(max_length=100, default='Patient')
    patient_role_fa = models.CharField(max_length=100, default='Patient')
    review_text_en = models.TextField()
    review_text_fa = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.patient_name_en}"

class AboutSection(models.Model):
    tag_en = models.CharField(max_length=100, default='ABOUT OUR HOSPITAL')
    tag_fa = models.CharField(max_length=100, default='ABOUT OUR HOSPITAL')
    title_en = models.CharField(max_length=255, default='Experience <b>Excellence</b> in Modern Healthcare')
    title_fa = models.CharField(max_length=255, default='Experience <b>Excellence</b> in Modern Healthcare')
    paragraph_1_en = models.TextField()
    paragraph_1_fa = models.TextField(blank=True)
    paragraph_2_en = models.TextField(blank=True)
    paragraph_2_fa = models.TextField(blank=True)
    feature_1_en = models.CharField(max_length=100, default='Expert Doctors')
    feature_1_fa = models.CharField(max_length=100, default='Expert Doctors')
    feature_2_en = models.CharField(max_length=100, default='24/7 Support')
    feature_2_fa = models.CharField(max_length=100, default='24/7 Support')
    feature_3_en = models.CharField(max_length=100, default='Modern Equipment')
    feature_3_fa = models.CharField(max_length=100, default='Modern Equipment')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "About Section Content"

class NavMenuItem(models.Model):
    label_en = models.CharField(max_length=100)
    label_fa = models.CharField(max_length=100)
    url = models.CharField(max_length=255, blank=True, null=True, help_text="Internal path like /services or external URL")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.PositiveIntegerField(default=0)
    icon_name = models.CharField(max_length=50, blank=True, null=True, help_text="Lucide icon name")
    is_active = models.BooleanField(default=True)
    is_mega_menu = models.BooleanField(default=False, help_text="If true, show categories/services in a wide dropdown")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label_en} ({self.label_fa})"


class ServiceFAQ(models.Model):
    service = models.ForeignKey(MedicalService, on_delete=models.CASCADE, related_name='faqs')
    question_en = models.CharField(max_length=255)
    question_fa = models.CharField(max_length=255)
    answer_en = models.TextField()
    answer_fa = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"FAQ: {self.question_en[:50]}..."
