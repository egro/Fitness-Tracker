from django.db import models
from django.contrib.auth.models import User


class ExerciseCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Exercise categories"
        unique_together = ["user", "name"]

    def __str__(self):
        return self.name


class Exercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    categories = models.ManyToManyField(ExerciseCategory, blank=True, related_name="exercises")
    notes = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "name"]

    def __str__(self):
        return self.name


class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weight_logs")
    date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"WeightLog {self.date}: {self.weight_kg}kg"


class MeasurementLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="measurements")
    date = models.DateField()
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    left_arm_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    right_arm_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    left_thigh_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    right_thigh_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    left_calf_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    right_calf_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    shoulders_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    neck_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"MeasurementLog {self.date}"


class WorkoutTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="templates")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkoutTemplateExercise(models.Model):
    template = models.ForeignKey(
        WorkoutTemplate, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    target_sets = models.PositiveIntegerField(null=True, blank=True)
    target_reps = models.CharField(max_length=50, blank=True)
    target_reps_min = models.PositiveIntegerField(null=True, blank=True)
    target_reps_max = models.PositiveIntegerField(null=True, blank=True)
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.template.name} - {self.exercise.name}"


class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workouts")
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    template = models.ForeignKey(
        WorkoutTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Workout {self.date} #{self.pk}"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE, related_name="exercises"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    target_sets = models.PositiveIntegerField(null=True, blank=True)
    target_reps_min = models.PositiveIntegerField(null=True, blank=True)
    target_reps_max = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.exercise.name} in {self.workout}"


class Set(models.Model):
    workout_exercise = models.ForeignKey(
        WorkoutExercise, on_delete=models.CASCADE, related_name="sets"
    )
    set_number = models.PositiveIntegerField()
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_warmup = models.BooleanField(default=False)

    class Meta:
        ordering = ["set_number"]

    def __str__(self):
        return f"Set {self.set_number}: {self.reps} reps @ {self.weight_kg}kg"


class BodyFatLog(models.Model):
    METHOD_CHOICES = [
        ("navy", "US Navy (calculated)"),
        ("caliper", "Caliper"),
        ("dexa", "DEXA Scan"),
        ("bodpod", "Bod Pod"),
        ("scale_bia", "Bioimpedance Scale"),
        ("photo_3d", "3D Photo Scan"),
        ("manual", "Manual Entry"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="body_fat_logs")
    date = models.DateField()
    body_fat_pct = models.FloatField("Body Fat %")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"BodyFatLog {self.date}: {self.body_fat_pct}% ({self.get_method_display()})"

    class Meta:
        ordering = ["-date", "-created_at"]


class CardioLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cardio_logs")
    date = models.DateField()
    activity = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()
    distance_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"CardioLog {self.date}: {self.activity} ({self.duration_minutes}min)"
