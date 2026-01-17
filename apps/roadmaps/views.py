"""
Views for Roadmaps app.
"""
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Roadmap, RoadmapStep
from .serializers import (
    RoadmapSerializer,
    RoadmapCreateSerializer,
    RoadmapStepSerializer,
    RoadmapStepUpdateSerializer,
)


class RoadmapViewSet(viewsets.ModelViewSet):
    """ViewSet for user roadmaps."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Roadmap.objects.filter(user=self.request.user).prefetch_related('steps')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoadmapCreateSerializer
        return RoadmapSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_step(self, request, pk=None):
        """Add a step to the roadmap."""
        roadmap = self.get_object()
        serializer = RoadmapStepSerializer(data=request.data)

        if serializer.is_valid():
            order = roadmap.steps.count()
            serializer.save(roadmap=roadmap, order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reorder_steps(self, request, pk=None):
        """Reorder steps in the roadmap."""
        roadmap = self.get_object()
        step_ids = request.data.get('step_ids', [])

        for idx, step_id in enumerate(step_ids):
            RoadmapStep.objects.filter(
                id=step_id,
                roadmap=roadmap
            ).update(order=idx)

        return Response({'message': 'Steps reordered successfully.'})

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get roadmap progress summary."""
        roadmap = self.get_object()
        steps = roadmap.steps.all()

        total = steps.count()
        completed = steps.filter(status='completed').count()
        in_progress = steps.filter(status='in_progress').count()

        return Response({
            'total_steps': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': total - completed - in_progress,
            'progress_percentage': round(completed / total * 100, 1) if total > 0 else 0,
        })


class RoadmapStepUpdateView(generics.UpdateAPIView):
    """Update a roadmap step status."""

    serializer_class = RoadmapStepUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RoadmapStep.objects.filter(roadmap__user=self.request.user)

    def perform_update(self, serializer):
        step = serializer.save()

        # If marking as completed, set completed_at
        if step.status == 'completed' and not step.completed_at:
            step.completed_at = timezone.now()
            step.save()

        # Update roadmap progress
        roadmap = step.roadmap
        total = roadmap.steps.count()
        completed = roadmap.steps.filter(status='completed').count()
        roadmap.progress = round(completed / total * 100) if total > 0 else 0
        roadmap.save()
