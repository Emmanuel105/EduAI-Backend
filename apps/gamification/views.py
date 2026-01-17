"""
Views for Gamification app.
"""
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import F
from django.utils import timezone

from .models import Badge, Achievement, UserGamification, UserAchievement, Leaderboard
from .serializers import (
    BadgeSerializer,
    AchievementSerializer,
    UserGamificationSerializer,
    LeaderboardEntrySerializer,
    UserLeaderboardSerializer,
    AddXPSerializer,
)


class BadgeListView(generics.ListAPIView):
    """List all available badges."""

    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [permissions.AllowAny]


class AchievementListView(generics.ListAPIView):
    """List all available achievements."""

    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [permissions.AllowAny]


class UserGamificationView(generics.RetrieveAPIView):
    """Get current user's gamification stats."""

    serializer_class = UserGamificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        gamification, _ = UserGamification.objects.get_or_create(user=self.request.user)
        return gamification


class UpdateStreakView(APIView):
    """Update user's streak and award bonus XP."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        gamification, _ = UserGamification.objects.get_or_create(user=request.user)

        old_streak = gamification.current_streak
        new_streak = gamification.update_streak()

        # Award streak bonus XP
        streak_bonus = 0
        if new_streak > old_streak:
            # Bonus XP based on streak length
            if new_streak >= 30:
                streak_bonus = 50
            elif new_streak >= 14:
                streak_bonus = 25
            elif new_streak >= 7:
                streak_bonus = 15
            elif new_streak >= 3:
                streak_bonus = 10
            else:
                streak_bonus = 5

            gamification.add_xp(streak_bonus)

            # Check streak achievements
            self._check_streak_achievements(gamification, new_streak)

        return Response({
            'current_streak': new_streak,
            'longest_streak': gamification.longest_streak,
            'streak_bonus_xp': streak_bonus,
        })

    def _check_streak_achievements(self, gamification, streak):
        """Check and update streak-based achievements."""
        streak_achievements = Achievement.objects.filter(type='STREAK', is_active=True)

        for achievement in streak_achievements:
            user_ach, created = UserAchievement.objects.get_or_create(
                user_gamification=gamification,
                achievement=achievement
            )
            if not user_ach.unlocked and streak >= achievement.requirement:
                user_ach.progress = streak
                user_ach.unlocked = True
                user_ach.unlocked_at = timezone.now()
                user_ach.save()
                gamification.add_xp(achievement.xp_reward)


class AddXPView(APIView):
    """Add XP to user (for internal use/testing)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddXPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        gamification, _ = UserGamification.objects.get_or_create(user=request.user)
        old_level = gamification.level

        new_xp = gamification.add_xp(serializer.validated_data['amount'])
        level_up = gamification.level > old_level

        return Response({
            'total_xp': new_xp,
            'level': gamification.level,
            'rank': gamification.rank,
            'level_up': level_up,
        })


class LeaderboardView(APIView):
    """Get leaderboard data."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        period = request.query_params.get('period', 'all_time')
        limit = min(int(request.query_params.get('limit', 10)), 100)

        # Get top users by XP
        top_users = UserGamification.objects.select_related('user').order_by('-total_xp')[:limit]

        leaderboard = []
        for rank, gam in enumerate(top_users, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': gam.user.id,
                'user_name': gam.user.name,
                'user_picture': gam.user.profile_picture,
                'total_xp': gam.total_xp,
                'level': gam.level,
            })

        # Get current user's rank if authenticated
        user_rank = None
        if request.user.is_authenticated:
            try:
                user_gam = request.user.gamification
                users_ahead = UserGamification.objects.filter(total_xp__gt=user_gam.total_xp).count()
                user_rank = {
                    'rank': users_ahead + 1,
                    'user_id': request.user.id,
                    'user_name': request.user.name,
                    'total_xp': user_gam.total_xp,
                    'level': user_gam.level,
                }
            except UserGamification.DoesNotExist:
                pass

        return Response({
            'period': period,
            'leaderboard': leaderboard,
            'user_rank': user_rank,
        })


class UserAchievementsView(APIView):
    """Get user's achievements with progress."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        gamification, _ = UserGamification.objects.get_or_create(user=request.user)

        # Get all achievements
        all_achievements = Achievement.objects.filter(is_active=True)

        # Get user's achievement progress
        user_achievements = {
            ua.achievement_id: ua
            for ua in UserAchievement.objects.filter(user_gamification=gamification)
        }

        result = {
            'unlocked': [],
            'in_progress': [],
            'locked': [],
        }

        for achievement in all_achievements:
            user_ach = user_achievements.get(achievement.id)

            achievement_data = {
                'id': achievement.id,
                'title': achievement.title,
                'description': achievement.description,
                'type': achievement.type,
                'requirement': achievement.requirement,
                'xp_reward': achievement.xp_reward,
                'icon': achievement.icon,
                'rarity': achievement.rarity,
            }

            if user_ach and user_ach.unlocked:
                achievement_data['unlocked_at'] = user_ach.unlocked_at
                result['unlocked'].append(achievement_data)
            elif user_ach and user_ach.progress > 0:
                achievement_data['progress'] = user_ach.progress
                achievement_data['progress_percentage'] = min(
                    100, round(user_ach.progress / achievement.requirement * 100, 1)
                )
                result['in_progress'].append(achievement_data)
            else:
                result['locked'].append(achievement_data)

        return Response(result)


class UserBadgesView(APIView):
    """Get user's badges."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        gamification, _ = UserGamification.objects.get_or_create(user=request.user)

        earned_badges = gamification.badges.all()
        all_badges = Badge.objects.all()

        earned_ids = set(earned_badges.values_list('id', flat=True))

        result = {
            'earned': BadgeSerializer(earned_badges, many=True).data,
            'available': BadgeSerializer(
                [b for b in all_badges if b.id not in earned_ids],
                many=True
            ).data,
        }

        return Response(result)
