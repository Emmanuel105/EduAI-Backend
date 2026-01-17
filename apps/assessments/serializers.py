"""
Serializers for Assessments app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Assessment, Question, AssessmentAttempt

User = get_user_model()


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions."""

    class Meta:
        model = Question
        fields = [
            'id', 'question', 'options', 'skill_category',
            'difficulty_level', 'points', 'explanation', 'order'
        ]


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Serializer for questions (hide correct answers for students)."""

    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'question', 'options', 'skill_category', 'difficulty_level', 'points', 'order']

    def get_options(self, obj):
        # Return options without isCorrect flag
        return [{'text': opt.get('text')} for opt in obj.options]


class InstructorBriefSerializer(serializers.ModelSerializer):
    """Brief instructor info."""

    class Meta:
        model = User
        fields = ['id', 'name', 'profile_picture']


class AssessmentListSerializer(serializers.ModelSerializer):
    """Serializer for assessment listings."""

    instructor = InstructorBriefSerializer(read_only=True)
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'instructor', 'field',
            'skills_assessed', 'difficulty', 'duration', 'passing_score',
            'status', 'total_attempts', 'average_score', 'questions_count',
            'created_at'
        ]

    def get_questions_count(self, obj):
        return obj.questions.count()


class AssessmentDetailSerializer(serializers.ModelSerializer):
    """Detailed assessment serializer with questions."""

    instructor = InstructorBriefSerializer(read_only=True)
    questions = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'instructor', 'field',
            'skills_assessed', 'difficulty', 'duration', 'passing_score',
            'status', 'total_attempts', 'average_score', 'top_skill_gaps',
            'questions', 'user_attempts', 'created_at', 'updated_at'
        ]

    def get_questions(self, obj):
        request = self.context.get('request')
        # Show correct answers only to instructor
        if request and request.user == obj.instructor:
            return QuestionSerializer(obj.questions.all(), many=True).data
        return QuestionStudentSerializer(obj.questions.all(), many=True).data

    def get_user_attempts(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = AssessmentAttempt.objects.filter(
                user=request.user,
                assessment=obj
            ).order_by('-started_at')[:5]
            return AssessmentAttemptBriefSerializer(attempts, many=True).data
        return []


class AssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assessments."""

    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'field', 'skills_assessed',
            'difficulty', 'duration', 'passing_score', 'questions'
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        assessment = Assessment.objects.create(**validated_data)

        for idx, question_data in enumerate(questions_data):
            question_data['order'] = idx
            Question.objects.create(assessment=assessment, **question_data)

        return assessment


class AssessmentAttemptBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for attempt listings."""

    class Meta:
        model = AssessmentAttempt
        fields = ['id', 'status', 'score', 'passed', 'time_taken', 'started_at', 'completed_at']


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    """Full serializer for assessment attempts."""

    assessment = AssessmentListSerializer(read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'status', 'score', 'passed',
            'time_taken', 'answers', 'skill_scores', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'score', 'passed', 'skill_scores', 'started_at', 'completed_at']


class SubmitAnswersSerializer(serializers.Serializer):
    """Serializer for submitting assessment answers."""

    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dict of {question_id: selected_option_index}"
    )
    time_taken = serializers.IntegerField(min_value=0, help_text="Time taken in seconds")


class AttemptResultSerializer(serializers.ModelSerializer):
    """Serializer for attempt results with detailed feedback."""

    assessment = AssessmentListSerializer(read_only=True)
    questions_feedback = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'assessment', 'status', 'score', 'passed',
            'time_taken', 'skill_scores', 'questions_feedback',
            'started_at', 'completed_at'
        ]

    def get_questions_feedback(self, obj):
        """Get detailed feedback for each question."""
        feedback = []
        questions = obj.assessment.questions.all()

        for question in questions:
            answer = obj.answers.get(str(question.id))
            correct_idx = None
            selected_correct = False

            for idx, option in enumerate(question.options):
                if option.get('isCorrect'):
                    correct_idx = idx
                    if answer is not None and int(answer) == idx:
                        selected_correct = True
                    break

            feedback.append({
                'question_id': question.id,
                'question': question.question,
                'selected_answer': answer,
                'correct_answer': correct_idx,
                'is_correct': selected_correct,
                'explanation': question.explanation,
                'skill_category': question.skill_category,
            })

        return feedback
