"""
Admin configuration for Gamification app.
"""
from django.contrib import admin
from .models import Badge, Achievement, UserGamification, UserBadge, UserAchievement, Leaderboard


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'rarity', 'xp_reward', 'created_at']
    list_filter = ['rarity']
    search_fields = ['name', 'description']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'requirement', 'xp_reward', 'rarity', 'is_active']
    list_filter = ['type', 'rarity', 'is_active']
    search_fields = ['title', 'description']


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0


@admin.register(UserGamification)
class UserGamificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_xp', 'level', 'rank', 'current_streak', 'longest_streak']
    list_filter = ['level', 'rank']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [UserBadgeInline, UserAchievementInline]


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'rank', 'xp_earned', 'updated_at']
    list_filter = ['period']
    search_fields = ['user__name']
