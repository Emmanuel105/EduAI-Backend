"""
URL patterns for Courses app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    CategoryViewSet,
    CourseViewSet,
    ModuleViewSet,
    EnrollmentListView,
    EnrollmentProgressView,
    InstructorCoursesView,
    DashboardView,
)

# Main router
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'', CourseViewSet, basename='course')

# Nested router for modules within courses
courses_router = nested_routers.NestedDefaultRouter(router, r'', lookup='course')
courses_router.register(r'modules', ModuleViewSet, basename='course-modules')

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Enrollments
    path('enrollments/', EnrollmentListView.as_view(), name='enrollment_list'),
    path('<slug:course_slug>/progress/', EnrollmentProgressView.as_view(), name='enrollment_progress'),

    # Instructor courses
    path('instructor/courses/', InstructorCoursesView.as_view(), name='instructor_courses'),

    # Router URLs
    path('', include(router.urls)),
    path('', include(courses_router.urls)),
]
