"""
Certificate models for EduAI.
"""
import uuid
from django.db import models
from django.conf import settings


class Certificate(models.Model):
    """Certificate for course completion."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='certificates'
    )

    # Unique certificate ID for verification
    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # Certificate details
    issued_date = models.DateTimeField(auto_now_add=True)
    certificate_url = models.URLField(blank=True, null=True)

    # Course snapshot at time of completion
    course_title = models.CharField(max_length=255)
    instructor_name = models.CharField(max_length=255)
    completion_date = models.DateField()

    # Additional metadata
    grade = models.CharField(max_length=10, blank=True, null=True)
    hours_completed = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        unique_together = ['user', 'course']
        ordering = ['-issued_date']

    def __str__(self):
        return f"{self.user.name} - {self.course_title}"

    def get_verification_url(self):
        """Generate verification URL."""
        return f"/api/certificates/verify/{self.certificate_id}/"
