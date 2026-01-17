"""
Course models for EduAI.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Course category model."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    """Course model."""

    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    poster = models.URLField(help_text="URL to course poster/thumbnail image")

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_created'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Course metadata
    duration_hours = models.PositiveIntegerField(
        default=0,
        help_text="Estimated course duration in hours"
    )
    language = models.CharField(max_length=50, default='English')
    prerequisites = models.TextField(blank=True, null=True)
    what_you_learn = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Statistics (cached for performance)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = f"{slugify(self.title)}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)


class Module(models.Model):
    """Module within a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )

    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)

    # Resources
    resources = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class ModuleQuiz(models.Model):
    """Quiz question within a module."""

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='quiz_questions'
    )

    question = models.TextField()
    options = models.JSONField(default=list)  # List of option strings
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Module Quiz Question'
        verbose_name_plural = 'Module Quiz Questions'
        ordering = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - Q{self.order + 1}"


class Enrollment(models.Model):
    """User enrollment in a course."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        DROPPED = 'dropped', 'Dropped'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    current_module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_enrollments'
    )

    # Track video progress per module: {module_id: percentage}
    video_progress = models.JSONField(default=dict, blank=True)

    # Track completed modules
    completed_modules = models.ManyToManyField(
        Module,
        blank=True,
        related_name='completed_by_enrollments'
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.name} - {self.course.title}"

    def calculate_progress(self):
        """Calculate course progress based on completed modules."""
        total_modules = self.course.modules.count()
        if total_modules == 0:
            return 0
        completed = self.completed_modules.count()
        self.progress = (completed / total_modules) * 100
        self.save(update_fields=['progress'])
        return self.progress


class CourseRating(models.Model):
    """User rating for a course."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_ratings'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='ratings'
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course Rating'
        verbose_name_plural = 'Course Ratings'
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.name} - {self.course.title}: {self.rating}/5"
