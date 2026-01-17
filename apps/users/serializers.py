"""
Serializers for User app.
"""
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""

    class Meta:
        model = UserProfile
        fields = [
            'preferred_learning_style',
            'learning_goals',
            'weekly_study_hours',
            'linkedin_url',
            'github_url',
            'website_url',
            'email_notifications',
            'push_notifications',
        ]


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer."""

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'profile_picture',
            'skills',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'date_joined']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with profile information."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'profile_picture',
            'bio',
            'phone',
            'skills',
            'github_linked',
            'google_linked',
            'is_active',
            'date_joined',
            'last_login',
            'profile',
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer with additional fields."""

    name = serializers.CharField(required=True, max_length=255)
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        default=User.Role.STUDENT,
        required=False
    )

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['name'] = self.validated_data.get('name', '')
        data['role'] = self.validated_data.get('role', User.Role.STUDENT)
        return data

    def save(self, request):
        user = super().save(request)
        user.name = self.validated_data.get('name', '')
        user.role = self.validated_data.get('role', User.Role.STUDENT)
        user.save()
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'name',
            'profile_picture',
            'bio',
            'phone',
            'skills',
            'profile',
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields if provided
        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class InstructorSerializer(serializers.ModelSerializer):
    """Serializer for instructor information."""

    courses_count = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'profile_picture',
            'bio',
            'skills',
            'courses_count',
            'students_count',
        ]

    def get_courses_count(self, obj):
        return obj.courses_created.count() if hasattr(obj, 'courses_created') else 0

    def get_students_count(self, obj):
        if hasattr(obj, 'courses_created'):
            return sum(course.enrollments.count() for course in obj.courses_created.all())
        return 0
