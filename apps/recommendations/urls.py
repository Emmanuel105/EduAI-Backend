"""
URL patterns for Recommendations app.
"""
from django.urls import path

from .views import (
    CourseRecommendationsView,
    TrendingCoursesView,
    SimilarCoursesView,
)

urlpatterns = [
    path('', CourseRecommendationsView.as_view(), name='recommendations'),
    path('trending/', TrendingCoursesView.as_view(), name='trending'),
    path('similar/<int:course_id>/', SimilarCoursesView.as_view(), name='similar'),
]
