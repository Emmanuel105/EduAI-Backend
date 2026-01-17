"""
Serializers for Gamification app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Badge, Achievement, UserGamification, UserBadge, UserAchievement, Leaderboard

User = get_user_model()


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model."""

    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon', 'rarity', 'xp_reward']


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model."""

    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'type', 'requirement', 'xp_reward', 'icon', 'rarity']


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for UserBadge."""

    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['badge', 'earned_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for UserAchievement."""

    achievement = AchievementSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = ['achievement', 'progress', 'unlocked', 'unlocked_at', 'progress_percentage']

    def get_progress_percentage(self, obj):
        if obj.achievement.requirement > 0:
            return min(100, round(obj.progress / obj.achievement.requirement * 100, 1))
        return 0


class UserGamificationSerializer(serializers.ModelSerializer):
    """Serializer for UserGamification."""

    badges = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    xp_for_next_level = serializers.SerializerMethodField()
    level_progress = serializers.SerializerMethodField()

    class Meta:
        model = UserGamification
        fields = [
            'total_xp', 'level', 'rank', 'current_streak', 'longest_streak',
            'last_activity_date', 'total_time_spent', 'badges', 'achievements',
            'xp_for_next_level', 'level_progress'
        ]

    def get_badges(self, obj):
        user_badges = UserBadge.objects.filter(user_gamification=obj).select_related('badge')
        return UserBadgeSerializer(user_badges, many=True).data

    def get_achievements(self, obj):
        user_achievements = UserAchievement.objects.filter(user_gamification=obj).select_related('achievement')
        return UserAchievementSerializer(user_achievements, many=True).data

    def get_xp_for_next_level(self, obj):
        return obj.get_xp_for_next_level()

    def get_level_progress(self, obj):
        """Calculate progress to next level as percentage."""
        current_level_xp = (obj.level - 1) ** 2 * 100
        next_level_xp = obj.level ** 2 * 100
        level_xp_range = next_level_xp - current_level_xp
        current_progress = obj.total_xp - current_level_xp
        return min(100, round(current_progress / level_xp_range * 100, 1)) if level_xp_range > 0 else 100


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for leaderboard entries."""

    user_name = serializers.CharField(source='user.name', read_only=True)
    user_picture = serializers.URLField(source='user.profile_picture', read_only=True)
    user_level = serializers.SerializerMethodField()

    class Meta:
        model = Leaderboard
        fields = ['rank', 'user_name', 'user_picture', 'user_level', 'xp_earned']

    def get_user_level(self, obj):
        try:
            return obj.user.gamification.level
        except UserGamification.DoesNotExist:
            return 1


class UserLeaderboardSerializer(serializers.Serializer):
    """Serializer for user's leaderboard position."""

    user_id = serializers.IntegerField(source='user.id')
    user_name = serializers.CharField(source='user.name')
    total_xp = serializers.IntegerField()
    level = serializers.IntegerField()
    rank = serializers.IntegerField()


class AddXPSerializer(serializers.Serializer):
    """Serializer for adding XP."""

    amount = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255, required=False)


class UpdateStreakSerializer(serializers.Serializer):
    """Serializer for streak update response."""

    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    streak_bonus_xp = serializers.IntegerField()
