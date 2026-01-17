"""
Views for Certificates app.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Certificate
from .serializers import CertificateSerializer, CertificateVerifySerializer
from apps.courses.models import Enrollment


class UserCertificatesView(generics.ListAPIView):
    """List user's certificates."""

    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user).select_related('course')


class CertificateDetailView(generics.RetrieveAPIView):
    """Get certificate details."""

    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'certificate_id'

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)


class CertificateVerifyView(generics.RetrieveAPIView):
    """Verify a certificate (public endpoint)."""

    serializer_class = CertificateVerifySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'certificate_id'
    queryset = Certificate.objects.all()


class GenerateCertificateView(APIView):
    """Generate certificate for a completed course."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        # Check enrollment and completion
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course_id=course_id,
            status='completed'
        )

        # Check if certificate already exists
        existing = Certificate.objects.filter(
            user=request.user,
            course=enrollment.course
        ).first()

        if existing:
            return Response(
                CertificateSerializer(existing).data,
                status=status.HTTP_200_OK
            )

        # Create certificate
        certificate = Certificate.objects.create(
            user=request.user,
            course=enrollment.course,
            course_title=enrollment.course.title,
            instructor_name=enrollment.course.instructor.name,
            completion_date=enrollment.completed_at.date() if enrollment.completed_at else timezone.now().date(),
            hours_completed=enrollment.course.duration_hours,
        )

        # TODO: Generate actual PDF certificate and upload to storage
        # certificate.certificate_url = generate_certificate_pdf(certificate)
        # certificate.save()

        return Response(
            CertificateSerializer(certificate).data,
            status=status.HTTP_201_CREATED
        )
