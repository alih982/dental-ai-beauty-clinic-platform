from rest_framework import serializers
from .models import LandingPageHeader, MedicalService, PatientReview, AboutSection, NavMenuItem, ServiceFAQ

class ServiceFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFAQ
        fields = ['id', 'question_en', 'question_fa', 'answer_en', 'answer_fa', 'order']

class LandingPageHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageHeader
        fields = [
            'id', 'title_en', 'title_fa', 'subtitle_en', 'subtitle_fa', 
            'search_placeholder_en', 'search_placeholder_fa', 
            'active_doctors_count', 'user_rating', 'is_active', 'updated_at'
        ]

class MedicalServiceSerializer(serializers.ModelSerializer):
    faqs = ServiceFAQSerializer(many=True, read_only=True)
    
    class Meta:
        model = MedicalService
        fields = '__all__'

class PatientReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientReview
        fields = [
            'id', 'patient_name_en', 'patient_name_fa', 
            'patient_role_en', 'patient_role_fa', 
            'review_text_en', 'review_text_fa', 
            'rating', 'image_url', 'is_active', 'created_at'
        ]

class AboutSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutSection
        fields = [
            'id', 'tag_en', 'tag_fa', 'title_en', 'title_fa', 
            'paragraph_1_en', 'paragraph_1_fa', 'paragraph_2_en', 'paragraph_2_fa', 
            'feature_1_en', 'feature_1_fa', 'feature_2_en', 'feature_2_fa', 
            'feature_3_en', 'feature_3_fa', 'is_active'
        ]

class NavMenuItemSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = NavMenuItem
        fields = ['id', 'label_en', 'label_fa', 'url', 'icon_name', 'is_mega_menu', 'children', 'order']

    def get_children(self, obj):
        if obj.children.exists():
            return NavMenuItemSerializer(obj.children.filter(is_active=True).order_by('order'), many=True).data
        return []
