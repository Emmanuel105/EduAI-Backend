"""
Serializers for Certificates app.
"""
from rest_framework import serializers
from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for Certificate model."""

    verification_url = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'user_name', 'course_title',
            'instructor_name', 'issued_date', 'completion_date',
            'certificate_url', 'grade', 'hours_completed', 'verification_url'
        ]

    def get_verification_url(self, obj):
        return obj.get_verification_url()


class CertificateVerifySerializer(serializers.ModelSerializer):
    """Serializer for certificate verification."""

    user_name = serializers.CharField(source='user.name', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'certificate_id', 'user_name', 'course_title',
            'instructor_name', 'issued_date', 'completion_date',
            'hours_completed', 'is_valid'
        ]

    def get_is_valid(self, obj):
        return True
