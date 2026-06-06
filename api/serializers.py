from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Profile, NavItem
from tracker.models import (
    ExerciseCategory, Exercise, WeightLog, MeasurementLog, BodyFatLog,
    WorkoutTemplate, WorkoutTemplateExercise, Workout, WorkoutExercise, Set,
    CardioLog,
)
from photos.models import ProgressPhoto


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "date_of_birth", "height_cm", "goal_weight_kg", "goal_body_fat_pct",
            "sex", "units", "theme", "nav_color",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined", "profile"]


class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ["id", "date", "weight_kg", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_weight_kg(self, value):
        if value is not None and (value <= 0 or value > 700):
            raise serializers.ValidationError("Weight must be between 0 and 700 kg.")
        return value


class MeasurementLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementLog
        fields = [
            "id", "date", "waist_cm", "chest_cm", "left_arm_cm", "right_arm_cm",
            "left_thigh_cm", "right_thigh_cm", "hips_cm", "left_calf_cm",
            "right_calf_cm", "shoulders_cm", "neck_cm", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BodyFatLogSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)

    class Meta:
        model = BodyFatLog
        fields = ["id", "date", "body_fat_pct", "method", "method_display", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_body_fat_pct(self, value):
        if value is not None and (value <= 0 or value >= 100):
            raise serializers.ValidationError("Body fat percentage must be between 0 and 100.")
        return value


class CardioLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardioLog
        fields = ["id", "date", "activity", "duration_minutes", "distance_km", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class ExerciseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class ExerciseSerializer(serializers.ModelSerializer):
    categories = ExerciseCategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=ExerciseCategory.objects.all(),
        source="categories", required=False,
    )

    class Meta:
        model = Exercise
        fields = ["id", "name", "categories", "category_ids", "notes", "is_public", "created_at"]
        read_only_fields = ["id", "created_at"]


class SetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fields = ["id", "set_number", "reps", "weight_kg", "is_warmup"]
        read_only_fields = ["id"]


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    sets = SetSerializer(many=True, read_only=True)
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = [
            "id", "exercise", "exercise_name", "order", "notes",
            "target_sets", "target_reps_min", "target_reps_max",
            "sets",
        ]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True, read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True, allow_null=True)

    class Meta:
        model = Workout
        fields = [
            "id", "date", "start_time", "end_time", "duration_minutes",
            "notes", "template", "template_name", "exercises", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class WorkoutListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()
    template_name = serializers.CharField(source="template.name", read_only=True, allow_null=True)

    class Meta:
        model = Workout
        fields = [
            "id", "date", "start_time", "end_time", "duration_minutes",
            "notes", "template", "template_name", "exercise_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_exercise_count(self, obj):
        return obj.exercises.count()


class WorkoutTemplateExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = WorkoutTemplateExercise
        fields = [
            "id", "exercise", "exercise_name", "order",
            "target_sets", "target_reps", "target_reps_min", "target_reps_max",
        ]
        read_only_fields = ["id"]


class WorkoutTemplateSerializer(serializers.ModelSerializer):
    exercises = WorkoutTemplateExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutTemplate
        fields = ["id", "name", "description", "is_public", "exercises", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProgressPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source="image", read_only=True)

    class Meta:
        model = ProgressPhoto
        fields = ["id", "date", "image", "image_url", "body_part", "notes", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]
