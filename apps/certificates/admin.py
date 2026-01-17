"""
Admin configuration for Certificates app.
"""
from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_title', 'instructor_name', 'issued_date', 'certificate_id']
    list_filter = ['issued_date']
    search_fields = ['user__name', 'user__email', 'course_title', 'certificate_id']
    readonly_fields = ['certificate_id', 'issued_date', 'created_at']
