"""
Gamification models for EduAI.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Badge(models.Model):
    """Badge that can be earned by users."""

    class Rarity(models.TextChoices):
        COMMON = 'common', 'Common'
        UNCOMMON = 'uncommon', 'Uncommon'
        RARE = 'rare', 'Rare'
        EPIC = 'epic', 'Epic'
        LEGENDARY = 'legendary', 'Legendary'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="Icon name or URL")
    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON
    )

    # XP reward for earning this badge
    xp_reward = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
        ordering = ['rarity', 'name']

    def __str__(self):
        return f"{self.name} ({self.rarity})"


class Achievement(models.Model):
    """Achievement that can be unlocked by users."""

    class Type(models.TextChoices):
        COURSE_COMPLETION = 'COURSE_COMPLETION', 'Course Completion'
        STREAK = 'STREAK', 'Streak'
        TIME_SPENT = 'TIME_SPENT', 'Time Spent'
        ASSESSMENT = 'ASSESSMENT', 'Assessment'
        ENROLLMENT = 'ENROLLMENT', 'Enrollment'
        PERFECT_SCORE = 'PERFECT_SCORE', 'Perfect Score'

    class Rarity(models.TextChoices):
        COMMON = 'common', 'Common'
        UNCOMMON = 'uncommon', 'Uncommon'
        RARE = 'rare', 'Rare'
        EPIC = 'epic', 'Epic'

    title = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=30, choices=Type.choices)
    requirement = models.PositiveIntegerField(
        help_text="Number required to unlock (e.g., 5 courses, 7 day streak)"
    )
    xp_reward = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=100)
    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
        ordering = ['type', 'requirement']

    def __str__(self):
        return f"{self.title} ({self.type})"


class UserGamification(models.Model):
    """User's gamification stats."""

    RANKS = [
        (0, 'Novice'),
        (100, 'Beginner'),
        (500, 'Learner'),
        (1000, 'Student'),
        (2500, 'Scholar'),
        (5000, 'Expert'),
        (10000, 'Master'),
        (25000, 'Grandmaster'),
        (50000, 'Legend'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gamification'
    )

    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    rank = models.CharField(max_length=50, default='Novice')

    # Streak tracking
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Time tracking
    total_time_spent = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent learning in minutes"
    )

    # Badges earned
    badges = models.ManyToManyField(
        Badge,
        through='UserBadge',
        related_name='users'
    )

    # Achievements unlocked
    achievements = models.ManyToManyField(
        Achievement,
        through='UserAchievement',
        related_name='users'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Gamification'
        verbose_name_plural = 'User Gamifications'

    def __str__(self):
        return f"{self.user.name} - Level {self.level} ({self.rank})"

    def add_xp(self, amount):
        """Add XP and recalculate level and rank."""
        self.total_xp += amount
        self.calculate_level()
        self.calculate_rank()
        self.save()
        return self.total_xp

    def calculate_level(self):
        """Calculate level based on XP. Level formula: sqrt(XP / 100)."""
        import math
        self.level = max(1, int(math.sqrt(self.total_xp / 100)) + 1)

    def calculate_rank(self):
        """Calculate rank based on XP thresholds."""
        for threshold, rank_name in reversed(self.RANKS):
            if self.total_xp >= threshold:
                self.rank = rank_name
                break

    def update_streak(self):
        """Update login/activity streak."""
        today = timezone.now().date()

        if self.last_activity_date is None:
            self.current_streak = 1
        elif self.last_activity_date == today:
            pass  # Already logged today
        elif self.last_activity_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1

        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_activity_date = today
        self.save()

        return self.current_streak

    def get_xp_for_next_level(self):
        """Calculate XP needed for next level."""
        next_level = self.level + 1
        xp_needed = (next_level - 1) ** 2 * 100
        return max(0, xp_needed - self.total_xp)


class UserBadge(models.Model):
    """Association between user and earned badge."""

    user_gamification = models.ForeignKey(
        UserGamification,
        on_delete=models.CASCADE,
        related_name='user_badges'
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Badge'
        verbose_name_plural = 'User Badges'
        unique_together = ['user_gamification', 'badge']

    def __str__(self):
        return f"{self.user_gamification.user.name} - {self.badge.name}"


class UserAchievement(models.Model):
    """Association between user and unlocked achievement."""

    user_gamification = models.ForeignKey(
        UserGamification,
        on_delete=models.CASCADE,
        related_name='user_achievements'
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0)
    unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'User Achievement'
        verbose_name_plural = 'User Achievements'
        unique_together = ['user_gamification', 'achievement']

    def __str__(self):
        status = "Unlocked" if self.unlocked else f"{self.progress}/{self.achievement.requirement}"
        return f"{self.user_gamification.user.name} - {self.achievement.title} ({status})"

    def update_progress(self, increment=1):
        """Update progress and check if achievement is unlocked."""
        if self.unlocked:
            return False

        self.progress += increment
        if self.progress >= self.achievement.requirement:
            self.unlocked = True
            self.unlocked_at = timezone.now()
            # Award XP
            self.user_gamification.add_xp(self.achievement.xp_reward)

        self.save()
        return self.unlocked


class Leaderboard(models.Model):
    """Cached leaderboard entries for performance."""

    class Period(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        ALL_TIME = 'all_time', 'All Time'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )
    period = models.CharField(max_length=20, choices=Period.choices)
    xp_earned = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField()

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leaderboard Entry'
        verbose_name_plural = 'Leaderboard Entries'
        unique_together = ['user', 'period']
        ordering = ['period', 'rank']

    def __str__(self):
        return f"{self.user.name} - #{self.rank} ({self.period})"
