"""
Assessment models for EduAI.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Assessment(models.Model):
    """Assessment/Test model."""

    class Difficulty(models.TextChoices):
        BEGINNER = 'Beginner', 'Beginner'
        INTERMEDIATE = 'Intermediate', 'Intermediate'
        ADVANCED = 'Advanced', 'Advanced'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments_created'
    )

    field = models.CharField(max_length=100, help_text="Subject/Field of assessment")
    skills_assessed = models.JSONField(default=list, help_text="List of skills being assessed")

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER
    )

    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
        validators=[MinValueValidator(1)]
    )

    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum score to pass (%)"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    # Statistics
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )

    # Top skill gaps identified
    top_skill_gaps = models.JSONField(
        default=list,
        blank=True,
        help_text="[{skill: string, gapPercentage: number}]"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.field})"


class Question(models.Model):
    """Question within an assessment."""

    class DifficultyLevel(models.TextChoices):
        EASY = 'Easy', 'Easy'
        MEDIUM = 'Medium', 'Medium'
        HARD = 'Hard', 'Hard'

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question = models.TextField()
    options = models.JSONField(
        default=list,
        help_text="[{text: string, isCorrect: boolean}]"
    )

    skill_category = models.CharField(max_length=100, blank=True, null=True)
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM
    )

    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['assessment', 'order']

    def __str__(self):
        return f"Q{self.order + 1}: {self.question[:50]}..."

    def get_correct_answer(self):
        """Get the correct option text."""
        for option in self.options:
            if option.get('isCorrect'):
                return option.get('text')
        return None


class AssessmentAttempt(models.Model):
    """User's attempt at an assessment."""

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ABANDONED = 'abandoned', 'Abandoned'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_attempts'
    )

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    passed = models.BooleanField(default=False)
    time_taken = models.PositiveIntegerField(default=0, help_text="Time taken in seconds")

    # Store answers: {question_id: selected_option_index}
    answers = models.JSONField(default=dict)

    # Skill analysis results
    skill_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text="{skill: score_percentage}"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Assessment Attempt'
        verbose_name_plural = 'Assessment Attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.name} - {self.assessment.title} ({self.score}%)"

    def calculate_score(self):
        """Calculate the score based on answers."""
        questions = self.assessment.questions.all()
        total_points = sum(q.points for q in questions)
        earned_points = 0
        skill_correct = {}
        skill_total = {}

        for question in questions:
            # Track skill performance
            skill = question.skill_category or 'General'
            skill_total[skill] = skill_total.get(skill, 0) + question.points

            # Check answer
            answer = self.answers.get(str(question.id))
            if answer is not None:
                try:
                    selected_option = question.options[int(answer)]
                    if selected_option.get('isCorrect'):
                        earned_points += question.points
                        skill_correct[skill] = skill_correct.get(skill, 0) + question.points
                except (IndexError, ValueError):
                    pass

        # Calculate overall score
        self.score = (earned_points / total_points * 100) if total_points > 0 else 0
        self.passed = self.score >= self.assessment.passing_score

        # Calculate skill scores
        for skill, total in skill_total.items():
            correct = skill_correct.get(skill, 0)
            self.skill_scores[skill] = round((correct / total * 100), 2) if total > 0 else 0

        self.save()
        return self.score
