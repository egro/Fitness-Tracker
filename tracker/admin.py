from django.contrib import admin
from .models import (
    ExerciseCategory,
    Exercise,
    WeightLog,
    MeasurementLog,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    Workout,
    WorkoutExercise,
    Set,
)


@admin.register(ExerciseCategory)
class ExerciseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "user"]
    list_filter = ["user"]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["name", "categories_list", "user"]
    list_filter = ["categories", "user"]

    def categories_list(self, obj):
        return ", ".join(c.name for c in obj.categories.all())
    categories_list.short_description = "Categories"


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "weight_kg"]
    list_filter = ["user", "date"]


@admin.register(MeasurementLog)
class MeasurementLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "waist_cm", "chest_cm"]
    list_filter = ["user"]


class WorkoutTemplateExerciseInline(admin.TabularInline):
    model = WorkoutTemplateExercise
    extra = 1


@admin.register(WorkoutTemplate)
class WorkoutTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "user"]
    inlines = [WorkoutTemplateExerciseInline]


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1


class SetInline(admin.TabularInline):
    model = Set
    extra = 0


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "template", "duration_minutes"]
    list_filter = ["user", "date"]


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ["workout", "exercise", "order"]
    inlines = [SetInline]


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ["workout_exercise", "set_number", "reps", "weight_kg"]
