"""
Roadmap models for EduAI.
"""
from django.db import models
from django.conf import settings


class Roadmap(models.Model):
    """Custom learning roadmap for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roadmaps'
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Roadmap content (can be JSON structure or markdown)
    content = models.TextField(help_text="Roadmap content in markdown or JSON format")

    # Target skill/career
    target_skill = models.CharField(max_length=100, blank=True, null=True)

    # Progress tracking
    is_active = models.BooleanField(default=True)
    progress = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Roadmap'
        verbose_name_plural = 'Roadmaps'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} - {self.name}"


class RoadmapStep(models.Model):
    """Individual step in a roadmap."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    # Optional link to a course
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roadmap_steps'
    )

    # Optional link to an assessment
    assessment = models.ForeignKey(
        'assessments.Assessment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roadmap_steps'
    )

    # External resource
    resource_url = models.URLField(blank=True, null=True)
    resource_type = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Roadmap Step'
        verbose_name_plural = 'Roadmap Steps'
        ordering = ['roadmap', 'order']

    def __str__(self):
        return f"{self.roadmap.name} - Step {self.order + 1}: {self.title}"
