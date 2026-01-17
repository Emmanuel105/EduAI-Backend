"""
Admin configuration for Roadmaps app.
"""
from django.contrib import admin
from .models import Roadmap, RoadmapStep


class RoadmapStepInline(admin.TabularInline):
    model = RoadmapStep
    extra = 1


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'target_skill', 'progress', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__name', 'target_skill']
    inlines = [RoadmapStepInline]


@admin.register(RoadmapStep)
class RoadmapStepAdmin(admin.ModelAdmin):
    list_display = ['title', 'roadmap', 'order', 'status', 'completed_at']
    list_filter = ['status']
    search_fields = ['title', 'roadmap__name']
