"""
URL patterns for Gamification app.
"""
from django.urls import path

from .views import (
    BadgeListView,
    AchievementListView,
    UserGamificationView,
    UpdateStreakView,
    AddXPView,
    LeaderboardView,
    UserAchievementsView,
    UserBadgesView,
)

urlpatterns = [
    # General endpoints
    path('badges/', BadgeListView.as_view(), name='badge_list'),
    path('achievements/', AchievementListView.as_view(), name='achievement_list'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),

    # User-specific endpoints
    path('me/', UserGamificationView.as_view(), name='user_gamification'),
    path('me/streak/', UpdateStreakView.as_view(), name='update_streak'),
    path('me/xp/', AddXPView.as_view(), name='add_xp'),
    path('me/achievements/', UserAchievementsView.as_view(), name='user_achievements'),
    path('me/badges/', UserBadgesView.as_view(), name='user_badges'),
]
