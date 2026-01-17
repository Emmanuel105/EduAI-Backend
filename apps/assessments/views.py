"""
Views for Assessments app.
"""
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg

from .models import Assessment, Question, AssessmentAttempt
from .serializers import (
    AssessmentListSerializer,
    AssessmentDetailSerializer,
    AssessmentCreateSerializer,
    QuestionSerializer,
    AssessmentAttemptSerializer,
    AssessmentAttemptBriefSerializer,
    SubmitAnswersSerializer,
    AttemptResultSerializer,
)


class IsInstructorOrReadOnly(permissions.BasePermission):
    """Allow instructors to create/edit, others can read."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'instructor'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.instructor == request.user


class AssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for assessments."""

    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        queryset = Assessment.objects.select_related('instructor')

        # Filter by status
        if not self.request.user.is_authenticated or self.request.user.role != 'instructor':
            queryset = queryset.filter(status='published')

        # Filter by field
        field = self.request.query_params.get('field')
        if field:
            queryset = queryset.filter(field__icontains=field)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by skill
        skill = self.request.query_params.get('skill')
        if skill:
            queryset = queryset.filter(skills_assessed__contains=skill)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.prefetch_related('questions')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AssessmentCreateSerializer
        elif self.action == 'retrieve':
            return AssessmentDetailSerializer
        return AssessmentListSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start(self, request, pk=None):
        """Start a new assessment attempt."""
        assessment = self.get_object()

        # Check for in-progress attempt
        existing = AssessmentAttempt.objects.filter(
            user=request.user,
            assessment=assessment,
            status='in_progress'
        ).first()

        if existing:
            return Response(
                AssessmentAttemptSerializer(existing).data,
                status=status.HTTP_200_OK
            )

        # Create new attempt
        attempt = AssessmentAttempt.objects.create(
            user=request.user,
            assessment=assessment
        )

        return Response(
            AssessmentAttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit(self, request, pk=None):
        """Submit answers for an assessment."""
        assessment = self.get_object()

        # Find in-progress attempt
        attempt = get_object_or_404(
            AssessmentAttempt,
            user=request.user,
            assessment=assessment,
            status='in_progress'
        )

        serializer = SubmitAnswersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save answers and calculate score
        attempt.answers = serializer.validated_data['answers']
        attempt.time_taken = serializer.validated_data['time_taken']
        attempt.status = AssessmentAttempt.Status.COMPLETED
        attempt.completed_at = timezone.now()
        attempt.save()

        attempt.calculate_score()

        # Update assessment statistics
        attempts = AssessmentAttempt.objects.filter(
            assessment=assessment,
            status='completed'
        )
        assessment.total_attempts = attempts.count()
        assessment.average_score = attempts.aggregate(Avg('score'))['score__avg'] or 0

        # Calculate skill gaps
        skill_gaps = {}
        for att in attempts:
            for skill, score in att.skill_scores.items():
                if skill not in skill_gaps:
                    skill_gaps[skill] = []
                skill_gaps[skill].append(100 - score)

        assessment.top_skill_gaps = [
            {'skill': skill, 'gapPercentage': round(sum(gaps) / len(gaps), 2)}
            for skill, gaps in sorted(skill_gaps.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)[:5]
        ]
        assessment.save()

        return Response(
            AttemptResultSerializer(attempt).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        """Publish an assessment."""
        assessment = self.get_object()

        if assessment.instructor != request.user:
            return Response(
                {'error': 'Only the instructor can publish.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if assessment.questions.count() == 0:
            return Response(
                {'error': 'Assessment must have at least one question.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assessment.status = 'published'
        assessment.save()

        return Response({'message': 'Assessment published successfully.'})


class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for questions within an assessment."""

    serializer_class = QuestionSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        assessment_id = self.kwargs.get('assessment_pk')
        return Question.objects.filter(assessment_id=assessment_id)

    def perform_create(self, serializer):
        assessment = get_object_or_404(Assessment, id=self.kwargs['assessment_pk'])
        order = assessment.questions.count()
        serializer.save(assessment=assessment, order=order)


class UserAttemptsView(generics.ListAPIView):
    """List current user's assessment attempts."""

    serializer_class = AssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssessmentAttempt.objects.filter(
            user=self.request.user
        ).select_related('assessment', 'assessment__instructor')


class AttemptDetailView(generics.RetrieveAPIView):
    """Get detailed results for an attempt."""

    serializer_class = AttemptResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssessmentAttempt.objects.filter(user=self.request.user)


class SkillAnalysisView(APIView):
    """Get skill analysis across all attempts."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        attempts = AssessmentAttempt.objects.filter(
            user=request.user,
            status='completed'
        )

        if not attempts.exists():
            return Response({
                'message': 'No completed assessments yet.',
                'skills': {}
            })

        # Aggregate skill scores
        skill_data = {}
        for attempt in attempts:
            for skill, score in attempt.skill_scores.items():
                if skill not in skill_data:
                    skill_data[skill] = {'scores': [], 'count': 0}
                skill_data[skill]['scores'].append(score)
                skill_data[skill]['count'] += 1

        # Calculate averages
        skills_summary = {}
        for skill, data in skill_data.items():
            avg_score = sum(data['scores']) / len(data['scores'])
            skills_summary[skill] = {
                'average_score': round(avg_score, 2),
                'attempts': data['count'],
                'trend': 'improving' if len(data['scores']) > 1 and data['scores'][-1] > data['scores'][0] else 'stable'
            }

        # Identify strengths and weaknesses
        sorted_skills = sorted(skills_summary.items(), key=lambda x: x[1]['average_score'], reverse=True)
        strengths = [s[0] for s in sorted_skills[:3] if s[1]['average_score'] >= 70]
        weaknesses = [s[0] for s in sorted_skills[-3:] if s[1]['average_score'] < 70]

        return Response({
            'skills': skills_summary,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'total_attempts': attempts.count(),
            'average_score': round(sum(a.score for a in attempts) / attempts.count(), 2)
        })
