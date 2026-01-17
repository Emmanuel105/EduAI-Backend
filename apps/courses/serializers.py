"""
Serializers for Courses app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Course, Module, ModuleQuiz, Enrollment, CourseRating

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'courses_count']

    def get_courses_count(self, obj):
        return obj.courses.filter(status='published').count()


class ModuleQuizSerializer(serializers.ModelSerializer):
    """Serializer for ModuleQuiz model."""

    class Meta:
        model = ModuleQuiz
        fields = ['id', 'question', 'options', 'correct_answer', 'explanation', 'order']


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module model."""

    quiz_questions = ModuleQuizSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'content', 'video_url', 'duration_minutes',
            'order', 'resources', 'quiz_questions'
        ]


class ModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating modules with nested quizzes."""

    quiz = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Module
        fields = ['id', 'title', 'content', 'video_url', 'duration_minutes', 'order', 'resources', 'quiz']

    def create(self, validated_data):
        quiz_data = validated_data.pop('quiz', [])
        module = Module.objects.create(**validated_data)

        for idx, quiz_item in enumerate(quiz_data):
            ModuleQuiz.objects.create(
                module=module,
                question=quiz_item.get('question', ''),
                options=quiz_item.get('options', []),
                correct_answer=quiz_item.get('correctAnswer', ''),
                order=idx
            )

        return module


class InstructorBriefSerializer(serializers.ModelSerializer):
    """Brief instructor info for course listings."""

    class Meta:
        model = User
        fields = ['id', 'name', 'profile_picture']


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course listings."""

    instructor = InstructorBriefSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'poster', 'instructor',
            'category', 'level', 'price', 'duration_hours', 'language',
            'average_rating', 'total_ratings', 'total_enrollments',
            'modules_count', 'created_at'
        ]

    def get_modules_count(self, obj):
        return obj.modules.count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed course serializer with modules."""

    instructor = InstructorBriefSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'poster', 'instructor',
            'category', 'level', 'price', 'status', 'duration_hours',
            'language', 'prerequisites', 'what_you_learn', 'tags',
            'average_rating', 'total_ratings', 'total_enrollments',
            'modules', 'is_enrolled', 'user_progress', 'created_at', 'updated_at'
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(user=request.user, course=obj).exists()
        return False

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(user=request.user, course=obj).first()
            if enrollment:
                return {
                    'progress': float(enrollment.progress),
                    'status': enrollment.status,
                    'current_module_id': enrollment.current_module_id,
                    'completed_modules': list(enrollment.completed_modules.values_list('id', flat=True))
                }
        return None


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating courses."""

    modules = ModuleCreateSerializer(many=True, required=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'title', 'description', 'poster', 'category_id', 'level',
            'price', 'duration_hours', 'language', 'prerequisites',
            'what_you_learn', 'tags', 'modules'
        ]

    def create(self, validated_data):
        modules_data = validated_data.pop('modules', [])
        category_id = validated_data.pop('category_id', None)

        if category_id:
            validated_data['category_id'] = category_id

        course = Course.objects.create(**validated_data)

        for idx, module_data in enumerate(modules_data):
            module_data['order'] = idx
            module_data['course'] = course
            quiz_data = module_data.pop('quiz', [])
            module = Module.objects.create(**module_data)

            for q_idx, quiz_item in enumerate(quiz_data):
                ModuleQuiz.objects.create(
                    module=module,
                    question=quiz_item.get('question', ''),
                    options=quiz_item.get('options', []),
                    correct_answer=quiz_item.get('correctAnswer', ''),
                    order=q_idx
                )

        return course


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for enrollment."""

    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'status', 'progress', 'current_module',
            'video_progress', 'enrolled_at', 'completed_at', 'last_accessed'
        ]
        read_only_fields = ['id', 'enrolled_at', 'completed_at', 'last_accessed']


class EnrollmentProgressSerializer(serializers.Serializer):
    """Serializer for updating enrollment progress."""

    module_id = serializers.IntegerField(required=False)
    video_progress = serializers.DictField(required=False)
    mark_complete = serializers.BooleanField(required=False, default=False)


class CourseRatingSerializer(serializers.ModelSerializer):
    """Serializer for course ratings."""

    user_name = serializers.CharField(source='user.name', read_only=True)
    user_picture = serializers.URLField(source='user.profile_picture', read_only=True)

    class Meta:
        model = CourseRating
        fields = ['id', 'rating', 'review', 'user_name', 'user_picture', 'created_at']
        read_only_fields = ['id', 'created_at']
