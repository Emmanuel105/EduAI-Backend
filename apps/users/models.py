"""
User models for EduAI.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for EduAI platform."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin'

    # Basic fields
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )

    # Profile fields
    profile_picture = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Skills for AI learning path recommendations
    skills = models.JSONField(default=list, blank=True)

    # Social auth identifiers
    firebase_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)
    github_linked = models.BooleanField(default=False)
    google_linked = models.BooleanField(default=False)

    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT


class UserProfile(models.Model):
    """Extended profile information for users."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Learning preferences
    preferred_learning_style = models.CharField(max_length=50, blank=True, null=True)
    learning_goals = models.JSONField(default=list, blank=True)
    weekly_study_hours = models.PositiveIntegerField(default=0)

    # Social links
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.name}"
