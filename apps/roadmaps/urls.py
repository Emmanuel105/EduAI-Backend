"""
URL patterns for Roadmaps app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RoadmapViewSet, RoadmapStepUpdateView

router = DefaultRouter()
router.register(r'', RoadmapViewSet, basename='roadmap')

urlpatterns = [
    path('steps/<int:pk>/', RoadmapStepUpdateView.as_view(), name='step_update'),
    path('', include(router.urls)),
]
