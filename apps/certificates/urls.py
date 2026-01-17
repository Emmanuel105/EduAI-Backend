"""
URL patterns for Certificates app.
"""
from django.urls import path

from .views import (
    UserCertificatesView,
    CertificateDetailView,
    CertificateVerifyView,
    GenerateCertificateView,
)

urlpatterns = [
    path('', UserCertificatesView.as_view(), name='user_certificates'),
    path('<uuid:certificate_id>/', CertificateDetailView.as_view(), name='certificate_detail'),
    path('verify/<uuid:certificate_id>/', CertificateVerifyView.as_view(), name='certificate_verify'),
    path('generate/<int:course_id>/', GenerateCertificateView.as_view(), name='generate_certificate'),
]
