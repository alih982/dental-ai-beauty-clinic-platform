from rest_framework import serializers
from apps.doctors.domain.models import Doctor, Specialty, DoctorWorkingHours

class SpecialtySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Specialty
        fields = ['id', 'name', 'name_en', 'name_fa', 'description', 'description_en', 'description_fa', 'icon']

    def get_name(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.name_fa if 'fa' in locale else obj.name_en

    def get_description(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.description_fa if 'fa' in locale else obj.description_en


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    specialty_name = serializers.SerializerMethodField()
    clinic_name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'specialty_name', 'specialty', 
            'rating', 'review_count', 'years_of_experience', 
            'clinic_name', 'city', 'fee', 'profile_image', 
            'is_verified', 'accepts_insurance'
        ]

    def get_full_name(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.get_full_name_fa() if 'fa' in locale else obj.get_full_name_en()

    def get_specialty_name(self, obj):
        if not obj.specialty:
            return None
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.specialty.name_fa if 'fa' in locale else obj.specialty.name_en

    def get_clinic_name(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.clinic_name_fa if 'fa' in locale else obj.clinic_name_en

    def get_city(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.city_fa if 'fa' in locale else obj.city_en


class DoctorWorkingHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorWorkingHours
        fields = ['day_of_week', 'day_name', 'start_time', 'end_time', 'is_active']


class DoctorDetailSerializer(DoctorListSerializer):
    bio = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    clinic_address = serializers.SerializerMethodField()
    sub_specialty = serializers.SerializerMethodField()
    working_hours = DoctorWorkingHoursSerializer(many=True, read_only=True)

    class Meta(DoctorListSerializer.Meta):
        fields = DoctorListSerializer.Meta.fields + [
            'bio', 'education', 'clinic_address', 'sub_specialty', 
            'email', 'medical_council_number', 'working_hours'
        ]

    def get_bio(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.bio_fa if 'fa' in locale else obj.bio_en

    def get_education(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.education_fa if 'fa' in locale else obj.education_en

    def get_clinic_address(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.clinic_address_fa if 'fa' in locale else obj.clinic_address_en

    def get_sub_specialty(self, obj):
        request = self.context.get('request')
        locale = request.headers.get('Accept-Language', 'en') if request else 'en'
        return obj.sub_specialty_fa if 'fa' in locale else obj.sub_specialty_en
