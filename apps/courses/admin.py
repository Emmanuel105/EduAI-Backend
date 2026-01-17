"""
Admin configuration for Courses app.
"""
from django.contrib import admin
from .models import Category, Course, Module, ModuleQuiz, Enrollment, CourseRating


class ModuleQuizInline(admin.TabularInline):
    model = ModuleQuiz
    extra = 1


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'level', 'status', 'price', 'total_enrollments']
    list_filter = ['status', 'level', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor__name']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    readonly_fields = ['total_enrollments', 'average_rating', 'total_ratings']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_minutes']
    list_filter = ['course']
    search_fields = ['title', 'course__title']
    inlines = [ModuleQuizInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'status', 'progress', 'enrolled_at']
    list_filter = ['status', 'enrolled_at']
    search_fields = ['user__name', 'user__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at']


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__name', 'course__title']
