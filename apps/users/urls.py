"""
URL patterns for User app.
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from dj_rest_auth.views import LoginView
from dj_rest_auth.registration.views import RegisterView

from .views import (
    ProfileView,
    PasswordChangeView,
    LogoutView,
    InstructorListView,
    InstructorDetailView,
    UserSkillsUpdateView,
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile endpoints
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/password/', PasswordChangeView.as_view(), name='password_change'),
    path('profile/skills/', UserSkillsUpdateView.as_view(), name='skills_update'),

    # Instructor endpoints
    path('instructors/', InstructorListView.as_view(), name='instructor_list'),
    path('instructors/<int:id>/', InstructorDetailView.as_view(), name='instructor_detail'),

    # Social auth (dj-rest-auth)
    path('social/', include('dj_rest_auth.registration.urls')),
]
