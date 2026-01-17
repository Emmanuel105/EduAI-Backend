"""
Admin configuration for Assessments app.
"""
from django.contrib import admin
from .models import Assessment, Question, AssessmentAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'field', 'difficulty', 'status', 'total_attempts', 'average_score']
    list_filter = ['status', 'difficulty', 'field', 'created_at']
    search_fields = ['title', 'description', 'instructor__name']
    inlines = [QuestionInline]
    readonly_fields = ['total_attempts', 'average_score']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'assessment', 'skill_category', 'difficulty_level', 'points']
    list_filter = ['difficulty_level', 'skill_category']
    search_fields = ['question', 'assessment__title']

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'assessment', 'status', 'score', 'passed', 'started_at', 'completed_at']
    list_filter = ['status', 'passed', 'started_at']
    search_fields = ['user__name', 'user__email', 'assessment__title']
    readonly_fields = ['started_at', 'completed_at']
