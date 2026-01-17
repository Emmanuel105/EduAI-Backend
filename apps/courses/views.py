"""
Views for Courses app.
"""
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg

from .models import Category, Course, Module, Enrollment, CourseRating
from .serializers import (
    CategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateSerializer,
    ModuleSerializer,
    EnrollmentSerializer,
    EnrollmentProgressSerializer,
    CourseRatingSerializer,
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


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for courses."""

    permission_classes = [IsInstructorOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Course.objects.select_related('instructor', 'category')

        # Filter by status (only published for non-instructors)
        if not self.request.user.is_authenticated or self.request.user.role != 'instructor':
            queryset = queryset.filter(status='published')

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        # Filter by instructor
        instructor = self.request.query_params.get('instructor')
        if instructor:
            queryset = queryset.filter(instructor_id=instructor)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.prefetch_related('modules')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user, status='draft')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, slug=None):
        """Enroll in a course."""
        course = self.get_object()

        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response(
                {'error': 'Already enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create enrollment
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            current_module=course.modules.first()
        )

        # Update course enrollment count
        course.total_enrollments += 1
        course.save(update_fields=['total_enrollments'])

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, slug=None):
        """Publish a course (instructor only)."""
        course = self.get_object()

        if course.instructor != request.user:
            return Response(
                {'error': 'Only the course instructor can publish.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if course.modules.count() == 0:
            return Response(
                {'error': 'Course must have at least one module to publish.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        course.status = 'published'
        course.save(update_fields=['status'])

        return Response({'message': 'Course published successfully.'})

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def ratings(self, request, slug=None):
        """Get or create course ratings."""
        course = self.get_object()

        if request.method == 'GET':
            ratings = CourseRating.objects.filter(course=course)
            return Response(CourseRatingSerializer(ratings, many=True).data)

        # POST - create or update rating
        serializer = CourseRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating, created = CourseRating.objects.update_or_create(
                user=request.user,
                course=course,
                defaults={
                    'rating': serializer.validated_data['rating'],
                    'review': serializer.validated_data.get('review', '')
                }
            )

            # Update course average rating
            avg = CourseRating.objects.filter(course=course).aggregate(Avg('rating'))
            course.average_rating = avg['rating__avg'] or 0
            course.total_ratings = CourseRating.objects.filter(course=course).count()
            course.save(update_fields=['average_rating', 'total_ratings'])

            return Response(
                CourseRatingSerializer(rating).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for modules within a course."""

    serializer_class = ModuleSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        return Module.objects.filter(course__slug=course_slug).prefetch_related('quiz_questions')

    def perform_create(self, serializer):
        course = get_object_or_404(Course, slug=self.kwargs['course_slug'])
        order = course.modules.count()
        serializer.save(course=course, order=order)


class EnrollmentListView(generics.ListAPIView):
    """List user's enrollments."""

    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related(
            'course', 'course__instructor', 'course__category'
        )


class EnrollmentProgressView(APIView):
    """Update enrollment progress."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_slug):
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course__slug=course_slug
        )

        serializer = EnrollmentProgressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Update current module
        if 'module_id' in data:
            module = get_object_or_404(Module, id=data['module_id'], course=enrollment.course)
            enrollment.current_module = module

        # Update video progress
        if 'video_progress' in data:
            enrollment.video_progress.update(data['video_progress'])

        # Mark module as complete
        if data.get('mark_complete') and enrollment.current_module:
            enrollment.completed_modules.add(enrollment.current_module)
            enrollment.calculate_progress()

            # Check if course is complete
            if enrollment.progress >= 100:
                enrollment.status = Enrollment.Status.COMPLETED
                enrollment.completed_at = timezone.now()

        enrollment.save()

        return Response(EnrollmentSerializer(enrollment).data)


class InstructorCoursesView(generics.ListAPIView):
    """List courses created by the current instructor."""

    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)


class DashboardView(APIView):
    """Dashboard data for the current user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get enrollments
        enrollments = Enrollment.objects.filter(user=user).select_related('course')
        active_enrollments = enrollments.filter(status='active')
        completed_enrollments = enrollments.filter(status='completed')

        # Calculate stats
        total_courses = enrollments.count()
        completed_courses = completed_enrollments.count()
        in_progress = active_enrollments.count()

        # Get recently accessed courses
        recent_courses = enrollments.order_by('-last_accessed')[:5]

        return Response({
            'stats': {
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'in_progress': in_progress,
                'completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
            },
            'recent_courses': EnrollmentSerializer(recent_courses, many=True).data,
            'active_courses': EnrollmentSerializer(active_enrollments[:5], many=True).data,
        })
