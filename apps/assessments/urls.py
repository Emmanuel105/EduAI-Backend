"""
URL patterns for Assessments app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    AssessmentViewSet,
    QuestionViewSet,
    UserAttemptsView,
    AttemptDetailView,
    SkillAnalysisView,
)

# Main router
router = DefaultRouter()
router.register(r'', AssessmentViewSet, basename='assessment')

# Nested router for questions
assessments_router = nested_routers.NestedDefaultRouter(router, r'', lookup='assessment')
assessments_router.register(r'questions', QuestionViewSet, basename='assessment-questions')

urlpatterns = [
    # User attempts
    path('attempts/', UserAttemptsView.as_view(), name='user_attempts'),
    path('attempts/<int:pk>/', AttemptDetailView.as_view(), name='attempt_detail'),

    # Skill analysis
    path('skills/analysis/', SkillAnalysisView.as_view(), name='skill_analysis'),

    # Router URLs
    path('', include(router.urls)),
    path('', include(assessments_router.urls)),
]
