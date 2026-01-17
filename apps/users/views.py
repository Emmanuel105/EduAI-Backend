"""
Views for User app.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UpdateProfileSerializer,
    PasswordChangeSerializer,
    InstructorSerializer,
)

User = get_user_model()


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UpdateProfileSerializer

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """Change user password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response(
                {'message': 'Password updated successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout user and blacklist refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            response = Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
            response.delete_cookie('token')
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class InstructorListView(generics.ListAPIView):
    """List all instructors."""

    serializer_class = InstructorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.INSTRUCTOR, is_active=True)


class InstructorDetailView(generics.RetrieveAPIView):
    """Get instructor details."""

    serializer_class = InstructorSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.filter(role=User.Role.INSTRUCTOR, is_active=True)


class UserSkillsUpdateView(APIView):
    """Update user skills for AI recommendations."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        skills = request.data.get('skills', [])
        if not isinstance(skills, list):
            return Response(
                {'error': 'Skills must be a list.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.skills = skills
        request.user.save()
        return Response(
            {'message': 'Skills updated successfully.', 'skills': skills},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'EduAI API',
        'version': '1.0.0'
    })
