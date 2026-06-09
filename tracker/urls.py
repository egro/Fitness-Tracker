from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Weight
    path("weight/add/", views.weight_add, name="weight_add"),
    path("weight/", views.weight_list, name="weight_list"),
    path("weight/<int:pk>/delete/", views.weight_delete, name="weight_delete"),
    # Measurements
    path("measurements/add/", views.measurement_add, name="measurement_add"),
    path("measurements/", views.measurement_list, name="measurement_list"),
    path(
        "measurements/<int:pk>/delete/",
        views.measurement_delete,
        name="measurement_delete",
    ),
    # Categories / Muscles
    path("categories/", views.category_list, name="category_list"),
    path("muscles/", views.muscle_list, name="muscle_list"),
    # Exercises
    path("exercises/", views.exercise_list, name="exercise_list"),
    path("exercises/add/", views.exercise_add, name="exercise_add"),
    path("exercises/<int:pk>/edit/", views.exercise_edit, name="exercise_edit"),
    path("exercises/<int:pk>/delete/", views.exercise_delete, name="exercise_delete"),
    # Templates
    path("templates/", views.template_list, name="template_list"),
    path("templates/add/", views.template_add, name="template_add"),
    path("templates/<int:pk>/", views.template_detail, name="template_detail"),
    path("templates/<int:pk>/edit/", views.template_edit, name="template_edit"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),
    path(
        "templates/<int:pk>/start/",
        views.template_start_workout,
        name="template_start_workout",
    ),
    # Workouts
    path("workouts/", views.workout_list, name="workout_list"),
    path("workouts/add/", views.workout_add, name="workout_add"),
    path("workouts/<int:pk>/", views.workout_detail, name="workout_detail"),
    path(
        "workouts/<int:pk>/add-exercise/",
        views.workout_exercise_add,
        name="workout_exercise_add",
    ),
    path(
        "workout-exercise/<int:pk>/remove/",
        views.workout_exercise_remove,
        name="workout_exercise_remove",
    ),
    path("workouts/<int:pk>/reorder/", views.workout_reorder, name="workout_reorder"),
    path("workouts/<int:pk>/finish/", views.workout_finish, name="workout_finish"),
    path("workouts/<int:pk>/delete/", views.workout_delete, name="workout_delete"),
    # Body Fat
    path("bodyfat/", views.body_fat_list, name="body_fat_list"),
    path("bodyfat/add/", views.body_fat_add, name="body_fat_add"),
    path("bodyfat/<int:pk>/delete/", views.body_fat_delete, name="body_fat_delete"),
    # Cardio
    path("cardio/", views.cardio_list, name="cardio_list"),
    path("cardio/add/", views.cardio_add, name="cardio_add"),
    path("cardio/<int:pk>/delete/", views.cardio_delete, name="cardio_delete"),
    # Sets (HTMX)
    path(
        "workout-exercise/<int:we_pk>/add-set/",
        views.set_add,
        name="set_add",
    ),
    path("set/<int:pk>/delete/", views.set_delete, name="set_delete"),
    path("set/<int:pk>/toggle/", views.set_toggle_complete, name="set_toggle"),
    path(
        "workout-exercise/<int:pk>/notes/",
        views.workout_exercise_notes,
        name="workout_exercise_notes",
    ),
    # Export / Import
    path("export/", views.export_data, name="import_export"),
    path("export/all/", views.export_all, name="export_all"),
    path("import/", views.import_data, name="import_data"),
]
