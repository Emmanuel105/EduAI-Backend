"""
Management command to seed initial achievements and badges.
"""
from django.core.management.base import BaseCommand
from apps.gamification.models import Achievement, Badge


class Command(BaseCommand):
    help = 'Seed initial achievements and badges'

    def handle(self, *args, **options):
        self.stdout.write('Seeding achievements and badges...')

        # Seed Achievements
        achievements_data = [
            # Course Completion
            {
                'title': 'First Steps',
                'description': 'Complete your first course',
                'type': 'COURSE_COMPLETION',
                'requirement': 1,
                'xp_reward': 100,
                'icon': 'trophy',
                'rarity': 'common',
            },
            {
                'title': 'Dedicated Learner',
                'description': 'Complete 5 courses',
                'type': 'COURSE_COMPLETION',
                'requirement': 5,
                'xp_reward': 500,
                'icon': 'star',
                'rarity': 'uncommon',
            },
            {
                'title': 'Knowledge Seeker',
                'description': 'Complete 10 courses',
                'type': 'COURSE_COMPLETION',
                'requirement': 10,
                'xp_reward': 1000,
                'icon': 'book-open',
                'rarity': 'rare',
            },
            {
                'title': 'Course Master',
                'description': 'Complete 25 courses',
                'type': 'COURSE_COMPLETION',
                'requirement': 25,
                'xp_reward': 2500,
                'icon': 'crown',
                'rarity': 'epic',
            },

            # Streak
            {
                'title': 'Getting Started',
                'description': 'Maintain a 3-day streak',
                'type': 'STREAK',
                'requirement': 3,
                'xp_reward': 50,
                'icon': 'fire',
                'rarity': 'common',
            },
            {
                'title': 'Week Warrior',
                'description': 'Maintain a 7-day streak',
                'type': 'STREAK',
                'requirement': 7,
                'xp_reward': 150,
                'icon': 'fire',
                'rarity': 'uncommon',
            },
            {
                'title': 'Consistency Champion',
                'description': 'Maintain a 30-day streak',
                'type': 'STREAK',
                'requirement': 30,
                'xp_reward': 500,
                'icon': 'fire',
                'rarity': 'rare',
            },
            {
                'title': 'Unstoppable',
                'description': 'Maintain a 100-day streak',
                'type': 'STREAK',
                'requirement': 100,
                'xp_reward': 2000,
                'icon': 'fire',
                'rarity': 'epic',
            },

            # Time Spent
            {
                'title': 'First Hour',
                'description': 'Spend 1 hour learning',
                'type': 'TIME_SPENT',
                'requirement': 60,  # minutes
                'xp_reward': 50,
                'icon': 'clock',
                'rarity': 'common',
            },
            {
                'title': 'Time Investor',
                'description': 'Spend 10 hours learning',
                'type': 'TIME_SPENT',
                'requirement': 600,
                'xp_reward': 300,
                'icon': 'clock',
                'rarity': 'uncommon',
            },
            {
                'title': 'Learning Marathon',
                'description': 'Spend 50 hours learning',
                'type': 'TIME_SPENT',
                'requirement': 3000,
                'xp_reward': 1000,
                'icon': 'clock',
                'rarity': 'rare',
            },

            # Assessment
            {
                'title': 'Quiz Taker',
                'description': 'Complete your first assessment',
                'type': 'ASSESSMENT',
                'requirement': 1,
                'xp_reward': 75,
                'icon': 'clipboard-check',
                'rarity': 'common',
            },
            {
                'title': 'Assessment Pro',
                'description': 'Complete 10 assessments',
                'type': 'ASSESSMENT',
                'requirement': 10,
                'xp_reward': 500,
                'icon': 'clipboard-check',
                'rarity': 'uncommon',
            },

            # Perfect Score
            {
                'title': 'Perfect Score',
                'description': 'Score 100% on an assessment',
                'type': 'PERFECT_SCORE',
                'requirement': 1,
                'xp_reward': 200,
                'icon': 'target',
                'rarity': 'rare',
            },
            {
                'title': 'Perfectionist',
                'description': 'Score 100% on 5 assessments',
                'type': 'PERFECT_SCORE',
                'requirement': 5,
                'xp_reward': 1000,
                'icon': 'target',
                'rarity': 'epic',
            },
        ]

        for ach_data in achievements_data:
            achievement, created = Achievement.objects.update_or_create(
                title=ach_data['title'],
                defaults=ach_data
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {achievement.title}')

        # Seed Badges
        badges_data = [
            {
                'name': 'Newcomer',
                'description': 'Welcome to EduAI! Start your learning journey.',
                'icon': 'user-plus',
                'rarity': 'common',
                'xp_reward': 10,
            },
            {
                'name': 'Fast Learner',
                'description': 'Complete a course within 24 hours of starting.',
                'icon': 'zap',
                'rarity': 'uncommon',
                'xp_reward': 100,
            },
            {
                'name': 'Social Butterfly',
                'description': 'Rate 10 courses with reviews.',
                'icon': 'message-circle',
                'rarity': 'uncommon',
                'xp_reward': 75,
            },
            {
                'name': 'Skill Master',
                'description': 'Achieve 90%+ in all skills of an assessment.',
                'icon': 'award',
                'rarity': 'rare',
                'xp_reward': 200,
            },
            {
                'name': 'Early Bird',
                'description': 'Complete a learning session before 7 AM.',
                'icon': 'sunrise',
                'rarity': 'uncommon',
                'xp_reward': 50,
            },
            {
                'name': 'Night Owl',
                'description': 'Complete a learning session after 11 PM.',
                'icon': 'moon',
                'rarity': 'uncommon',
                'xp_reward': 50,
            },
            {
                'name': 'Polyglot',
                'description': 'Complete courses in 3 different categories.',
                'icon': 'globe',
                'rarity': 'rare',
                'xp_reward': 150,
            },
            {
                'name': 'Helping Hand',
                'description': 'Help other learners by answering questions.',
                'icon': 'hand-holding',
                'rarity': 'uncommon',
                'xp_reward': 100,
            },
            {
                'name': 'Legend',
                'description': 'Reach the Legend rank.',
                'icon': 'crown',
                'rarity': 'legendary',
                'xp_reward': 1000,
            },
        ]

        for badge_data in badges_data:
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {badge.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully seeded {len(achievements_data)} achievements and {len(badges_data)} badges!'
        ))
