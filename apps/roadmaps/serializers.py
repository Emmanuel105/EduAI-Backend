"""
Serializers for Roadmaps app.
"""
from rest_framework import serializers
from .models import Roadmap, RoadmapStep
from apps.courses.serializers import CourseListSerializer


class RoadmapStepSerializer(serializers.ModelSerializer):
    """Serializer for RoadmapStep."""

    course_title = serializers.CharField(source='course.title', read_only=True)
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)

    class Meta:
        model = RoadmapStep
        fields = [
            'id', 'title', 'description', 'order', 'course', 'course_title',
            'assessment', 'assessment_title', 'resource_url', 'resource_type',
            'status', 'completed_at'
        ]


class RoadmapSerializer(serializers.ModelSerializer):
    """Serializer for Roadmap."""

    steps = RoadmapStepSerializer(many=True, read_only=True)
    steps_count = serializers.SerializerMethodField()
    completed_steps = serializers.SerializerMethodField()

    class Meta:
        model = Roadmap
        fields = [
            'id', 'name', 'description', 'content', 'target_skill',
            'is_active', 'progress', 'steps', 'steps_count', 'completed_steps',
            'created_at', 'updated_at'
        ]

    def get_steps_count(self, obj):
        return obj.steps.count()

    def get_completed_steps(self, obj):
        return obj.steps.filter(status='completed').count()


class RoadmapCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating roadmaps."""

    steps = RoadmapStepSerializer(many=True, required=False)

    class Meta:
        model = Roadmap
        fields = ['name', 'description', 'content', 'target_skill', 'steps']

    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        roadmap = Roadmap.objects.create(**validated_data)

        for idx, step_data in enumerate(steps_data):
            step_data['order'] = idx
            RoadmapStep.objects.create(roadmap=roadmap, **step_data)

        return roadmap


class RoadmapStepUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating roadmap step status."""

    class Meta:
        model = RoadmapStep
        fields = ['status']
