"""
Views for AI-powered course recommendations.
"""
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Q

from apps.courses.models import Course, Enrollment, CourseRating
from apps.courses.serializers import CourseListSerializer
from apps.assessments.models import AssessmentAttempt


class CourseRecommendationsView(APIView):
    """Get personalized course recommendations."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 10))

        # Get user's enrolled course IDs
        enrolled_ids = Enrollment.objects.filter(
            user=user
        ).values_list('course_id', flat=True)

        # Get user's skills and interests
        user_skills = set(user.skills or [])

        # Base queryset - exclude already enrolled courses
        queryset = Course.objects.filter(
            status='published'
        ).exclude(
            id__in=enrolled_ids
        ).select_related('instructor', 'category')

        recommendations = []

        # 1. Skill-based recommendations
        if user_skills:
            skill_matches = queryset.filter(
                Q(tags__overlap=list(user_skills)) |
                Q(title__icontains=list(user_skills)[0] if user_skills else '')
            ).annotate(
                enrollment_count=Count('enrollments')
            ).order_by('-enrollment_count', '-average_rating')[:limit]

            recommendations.extend([
                {'course': c, 'reason': 'Matches your skills', 'score': 0.9}
                for c in skill_matches
            ])

        # 2. Based on completed courses - similar category/level
        completed_enrollments = Enrollment.objects.filter(
            user=user,
            status='completed'
        ).select_related('course')

        if completed_enrollments.exists():
            completed_categories = set(
                e.course.category_id for e in completed_enrollments if e.course.category_id
            )
            completed_levels = set(e.course.level for e in completed_enrollments)

            # Recommend next level courses in same categories
            level_progression = {
                'beginner': 'intermediate',
                'intermediate': 'advanced',
            }

            for level in completed_levels:
                next_level = level_progression.get(level)
                if next_level:
                    progression_courses = queryset.filter(
                        category_id__in=completed_categories,
                        level=next_level
                    ).order_by('-average_rating')[:3]

                    recommendations.extend([
                        {'course': c, 'reason': 'Continue your learning journey', 'score': 0.85}
                        for c in progression_courses
                    ])

        # 3. Popular courses in categories user has shown interest
        if enrolled_ids:
            enrolled_categories = Course.objects.filter(
                id__in=enrolled_ids
            ).values_list('category_id', flat=True).distinct()

            popular_in_category = queryset.filter(
                category_id__in=enrolled_categories
            ).order_by('-total_enrollments', '-average_rating')[:5]

            recommendations.extend([
                {'course': c, 'reason': 'Popular in categories you like', 'score': 0.7}
                for c in popular_in_category
            ])

        # 4. Based on assessment weaknesses
        attempts = AssessmentAttempt.objects.filter(
            user=user,
            status='completed'
        )

        weak_skills = set()
        for attempt in attempts:
            for skill, score in attempt.skill_scores.items():
                if score < 60:
                    weak_skills.add(skill.lower())

        if weak_skills:
            skill_improvement = queryset.filter(
                Q(tags__overlap=list(weak_skills)) |
                Q(title__icontains=list(weak_skills)[0])
            )[:3]

            recommendations.extend([
                {'course': c, 'reason': 'Improve your weak areas', 'score': 0.8}
                for c in skill_improvement
            ])

        # 5. Trending/highly rated courses as fallback
        trending = queryset.order_by('-total_enrollments', '-average_rating')[:5]
        recommendations.extend([
            {'course': c, 'reason': 'Trending now', 'score': 0.5}
            for c in trending
        ])

        # Deduplicate and sort by score
        seen_ids = set()
        unique_recommendations = []
        for rec in sorted(recommendations, key=lambda x: x['score'], reverse=True):
            if rec['course'].id not in seen_ids:
                seen_ids.add(rec['course'].id)
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        # Serialize response
        result = []
        for rec in unique_recommendations:
            course_data = CourseListSerializer(rec['course']).data
            course_data['recommendation_reason'] = rec['reason']
            result.append(course_data)

        return Response({
            'recommendations': result,
            'based_on': {
                'skills': list(user_skills),
                'completed_courses': completed_enrollments.count(),
                'weak_areas': list(weak_skills) if weak_skills else [],
            }
        })


class TrendingCoursesView(APIView):
    """Get trending courses."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        category = request.query_params.get('category')

        queryset = Course.objects.filter(status='published')

        if category:
            queryset = queryset.filter(category__slug=category)

        trending = queryset.order_by('-total_enrollments', '-average_rating')[:limit]

        return Response({
            'courses': CourseListSerializer(trending, many=True).data
        })


class SimilarCoursesView(APIView):
    """Get courses similar to a given course."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, course_id):
        limit = int(request.query_params.get('limit', 5))

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=404)

        # Find similar courses based on category, level, and tags
        similar = Course.objects.filter(
            status='published'
        ).exclude(
            id=course_id
        ).filter(
            Q(category=course.category) |
            Q(level=course.level) |
            Q(tags__overlap=course.tags)
        ).order_by('-average_rating')[:limit]

        return Response({
            'courses': CourseListSerializer(similar, many=True).data
        })
