import csv
import json
from datetime import date, timedelta
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Max
from .models import (
    ExerciseCategory, Exercise, WeightLog, MeasurementLog,
    WorkoutTemplate, WorkoutTemplateExercise, Workout, WorkoutExercise, Set,
)
from .utils import convert_weight, convert_length, weight_unit, length_unit


def _weight_data(user, days=30):
    cutoff = date.today() - timedelta(days=days)
    logs = WeightLog.objects.filter(user=user, date__gte=cutoff).order_by("date")
    labels = [str(l.date) for l in logs]
    values = []
    for l in logs:
        v = float(l.weight_kg)
        if user.profile.units == "imperial":
            v = round(v * 2.20462, 1)
        values.append(v)
    return labels, values


def _measurement_data(user, days=180):
    cutoff = date.today() - timedelta(days=days)
    logs = MeasurementLog.objects.filter(user=user, date__gte=cutoff).order_by("date")
    labels = [str(l.date) for l in logs]

    fields = [
        ("waist_cm", "Waist"),
        ("chest_cm", "Chest"),
        ("left_arm_cm", "L Arm"),
        ("right_arm_cm", "R Arm"),
        ("left_thigh_cm", "L Thigh"),
        ("right_thigh_cm", "R Thigh"),
        ("hips_cm", "Hips"),
        ("left_calf_cm", "L Calf"),
        ("right_calf_cm", "R Calf"),
        ("shoulders_cm", "Shoulders"),
        ("neck_cm", "Neck"),
    ]

    color_map = {
        "waist_cm": "#3b82f6",
        "chest_cm": "#ef4444",
        "left_arm_cm": "#16a34a",
        "right_arm_cm": "#86efac",
        "left_thigh_cm": "#9333ea",
        "right_thigh_cm": "#c084fc",
        "hips_cm": "#f97316",
        "left_calf_cm": "#db2777",
        "right_calf_cm": "#f472b6",
        "shoulders_cm": "#14b8a6",
        "neck_cm": "#f59e0b",
    }

    has_data = len(labels) > 0
    datasets = []
    for field, label in fields:
        values = []
        for log in logs:
            val = getattr(log, field)
            if val is not None:
                v = float(val)
                if user.profile.units == "imperial":
                    v = round(v * 0.393701, 1)
                values.append(v)
            else:
                values.append(None)
        datasets.append({
            "label": label,
            "data": values,
            "borderColor": color_map[field],
            "backgroundColor": color_map[field] + "33",
            "tension": 0.3,
            "spanGaps": False,
        })

    return json.dumps(labels) if has_data else "[]", json.dumps(datasets) if has_data else "[]", has_data


@login_required
def dashboard(request):
    recent_weight = WeightLog.objects.filter(user=request.user).order_by("-date")[:7]
    recent_measurements = MeasurementLog.objects.filter(user=request.user).order_by("-date")[:5]
    recent_workouts = Workout.objects.filter(user=request.user).order_by("-date")[:5]
    weight_labels, weight_values = _weight_data(request.user, 180)

    last_weight = recent_weight.first()
    week_ago_weight = WeightLog.objects.filter(
        user=request.user,
        date__gte=date.today() - timedelta(days=8),
    ).exclude(pk=last_weight.pk if last_weight else None).order_by("-date").first()

    weight_change = None
    if last_weight and week_ago_weight:
        weight_change = float(last_weight.weight_kg) - float(week_ago_weight.weight_kg)
        if request.user.profile.units == "imperial":
            weight_change = round(weight_change * 2.20462, 1)

    has_weight_data = bool(weight_labels)
    meas_labels, meas_datasets, has_meas_data = _measurement_data(request.user, 180)
    ctx = {
        "recent_weight": recent_weight,
        "recent_measurements": recent_measurements,
        "recent_workouts": recent_workouts,
        "weight_labels": json.dumps(weight_labels) if has_weight_data else "[]",
        "weight_values": json.dumps(weight_values) if has_weight_data else "[]",
        "has_weight_data": has_weight_data,
        "last_weight": last_weight,
        "weight_change": weight_change,
        "meas_labels": meas_labels,
        "meas_datasets": meas_datasets,
        "has_meas_data": has_meas_data,
        "wu": weight_unit(request.user),
        "lu": length_unit(request.user),
    }
    return render(request, "tracker/dashboard.html", ctx)


# ── Weight ──────────────────────────────────────────────────────

@login_required
def weight_add(request):
    if request.method == "POST":
        date_val = request.POST.get("date", date.today())
        weight_val = request.POST.get("weight") or request.POST.get("weight_kg")
        weight_lbs = request.POST.get("weight_lbs")
        notes_val = request.POST.get("notes", "")
        if weight_val:
            weight_kg = float(weight_val)
        elif weight_lbs:
            weight_kg = float(weight_lbs) / 2.20462
        else:
            weight_kg = None
        if weight_kg is not None:
            WeightLog.objects.update_or_create(
                user=request.user,
                date=date_val,
                defaults={"weight_kg": round(weight_kg, 2), "notes": notes_val},
            )
            messages.success(request, "Weight logged!")
            return redirect("tracker:weight_list")
    return render(request, "tracker/weight_form.html", {
        "today": date.today(),
        "max_date": date.today(),
        "wu": weight_unit(request.user),
    })


@login_required
def weight_list(request):
    logs = WeightLog.objects.filter(user=request.user).order_by("-date")
    labels, values = _weight_data(request.user, 90)
    has_weight_data = bool(labels)
    return render(request, "tracker/weight_list.html", {
        "logs": logs,
        "labels": json.dumps(labels) if has_weight_data else "[]",
        "values": json.dumps(values) if has_weight_data else "[]",
        "has_weight_data": has_weight_data,
        "wu": weight_unit(request.user),
    })


@login_required
def weight_delete(request, pk):
    log = get_object_or_404(WeightLog, pk=pk, user=request.user)
    log.delete()
    messages.success(request, "Weight entry deleted.")
    return redirect("tracker:weight_list")


# ── Measurements ────────────────────────────────────────────────

@login_required
def measurement_add(request):
    if request.method == "POST":
        data = {k: request.POST.get(k) or None for k in [
            "waist_cm", "chest_cm", "left_arm_cm", "right_arm_cm",
            "left_thigh_cm", "right_thigh_cm", "hips_cm",
            "left_calf_cm", "right_calf_cm", "shoulders_cm", "neck_cm",
        ]}
        for k in data:
            if data[k] is not None:
                val = float(data[k])
                if request.user.profile.units == "imperial":
                    val = val / 2.54
                data[k] = round(val, 1)

        MeasurementLog.objects.update_or_create(
            user=request.user,
            date=request.POST.get("date", date.today()),
            defaults={**data, "notes": request.POST.get("notes", "")},
        )
        messages.success(request, "Measurements saved!")
        return redirect("tracker:measurement_list")
    return render(request, "tracker/measurement_form.html", {
        "today": date.today(),
        "max_date": date.today(),
        "lu": length_unit(request.user),
    })


@login_required
def measurement_list(request):
    logs = MeasurementLog.objects.filter(user=request.user).order_by("-date")
    return render(request, "tracker/measurement_list.html", {
        "logs": logs,
        "lu": length_unit,
        "convert_length": convert_length,
    })


@login_required
def measurement_delete(request, pk):
    log = get_object_or_404(MeasurementLog, pk=pk, user=request.user)
    log.delete()
    messages.success(request, "Measurement entry deleted.")
    return redirect("tracker:measurement_list")


# ── Exercises ───────────────────────────────────────────────────

@login_required
def exercise_list(request):
    categories = ExerciseCategory.objects.filter(
        user__in=[request.user, None]
    ).distinct()
    exercises = Exercise.objects.filter(
        user__in=[request.user, None]
    ).select_related("category").order_by("category__name", "name")
    return render(request, "tracker/exercise_list.html", {
        "categories": categories,
        "exercises": exercises,
    })


@login_required
def exercise_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        new_category_name = request.POST.get("new_category", "").strip()
        notes = request.POST.get("notes", "")
        cat = None
        if category_id == "__new__" and new_category_name:
            cat, _ = ExerciseCategory.objects.get_or_create(
                user=request.user, name=new_category_name,
            )
        elif category_id:
            cat = ExerciseCategory.objects.filter(
                pk=category_id, user__in=[request.user, None]
            ).first()
        if name:
            Exercise.objects.get_or_create(
                user=request.user, name=name,
                defaults={"category": cat, "notes": notes},
            )
            messages.success(request, f"Exercise '{name}' added!")
            return redirect("tracker:exercise_list")
    return render(request, "tracker/exercise_form.html", {
        "categories": ExerciseCategory.objects.filter(
            user__in=[request.user, None]
        ).distinct(),
    })


@login_required
def exercise_delete(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    exercise.delete()
    messages.success(request, "Exercise deleted.")
    return redirect("tracker:exercise_list")


# ── Workout Templates ──────────────────────────────────────────

@login_required
def template_list(request):
    templates = WorkoutTemplate.objects.filter(user=request.user).order_by("name")
    return render(request, "tracker/template_list.html", {"templates": templates})


@login_required
def template_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        exercise_ids = request.POST.getlist("exercises")
        if name:
            tpl = WorkoutTemplate.objects.create(
                user=request.user, name=name, description=description
            )
            for i, eid in enumerate(exercise_ids):
                if eid:
                    exercise = Exercise.objects.filter(pk=eid).first()
                    if exercise:
                        WorkoutTemplateExercise.objects.create(
                            template=tpl, exercise=exercise, order=i
                        )
            messages.success(request, f"Template '{name}' created!")
            return redirect("tracker:template_list")
    exercises = Exercise.objects.filter(
        user__in=[request.user, None]
    ).order_by("name")
    return render(request, "tracker/template_form.html", {"exercises": exercises})


@login_required
def template_detail(request, pk):
    tpl = get_object_or_404(WorkoutTemplate, pk=pk, user=request.user)
    ctx = {
        "template": tpl,
        "wu": weight_unit,
        "convert_weight": convert_weight,
    }
    return render(request, "tracker/template_detail.html", ctx)


@login_required
def template_delete(request, pk):
    tpl = get_object_or_404(WorkoutTemplate, pk=pk, user=request.user)
    tpl.delete()
    messages.success(request, "Template deleted.")
    return redirect("tracker:template_list")


@login_required
def template_start_workout(request, pk):
    tpl = get_object_or_404(WorkoutTemplate, pk=pk, user=request.user)
    workout = Workout.objects.create(user=request.user, date=date.today(), template=tpl)
    for te in tpl.exercises.select_related("exercise").all():
        WorkoutExercise.objects.create(
            workout=workout, exercise=te.exercise, order=te.order
        )
    return redirect("tracker:workout_detail", pk=workout.pk)


# ── Workouts ───────────────────────────────────────────────────

@login_required
def workout_list(request):
    workouts = Workout.objects.filter(user=request.user).order_by("-date", "-created_at")
    return render(request, "tracker/workout_list.html", {"workouts": workouts})


@login_required
def workout_add(request):
    templates = WorkoutTemplate.objects.filter(user=request.user).order_by("name")
    if request.method == "POST":
        template_id = request.POST.get("template")
        if template_id:
            return redirect("tracker:template_start_workout", pk=template_id)
        else:
            workout = Workout.objects.create(user=request.user, date=request.POST.get("date", date.today()))
            return redirect("tracker:workout_detail", pk=workout.pk)
    return render(request, "tracker/workout_form.html", {
        "templates": templates,
        "today": date.today(),
        "max_date": date.today(),
    })


@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    exercises = workout.exercises.select_related("exercise").prefetch_related("sets").all()
    all_exercises = Exercise.objects.filter(
        user__in=[request.user, None]
    ).order_by("name")
    return render(request, "tracker/workout_detail.html", {
        "workout": workout,
        "workout_exercises": exercises,
        "all_exercises": all_exercises,
        "wu": weight_unit,
        "lu": length_unit,
        "convert_weight": convert_weight,
    })


@login_required
def workout_exercise_add(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        exercise_id = request.POST.get("exercise")
        if exercise_id:
            exercise = get_object_or_404(Exercise, pk=exercise_id)
            max_order = workout.exercises.aggregate(m=Max("order"))["m"] or 0
            WorkoutExercise.objects.create(
                workout=workout, exercise=exercise, order=max_order + 1
            )
    return redirect("tracker:workout_detail", pk=workout.pk)


@login_required
def workout_exercise_remove(request, pk):
    we = get_object_or_404(WorkoutExercise, pk=pk, workout__user=request.user)
    workout_pk = we.workout.pk
    we.delete()
    return redirect("tracker:workout_detail", pk=workout_pk)


@login_required
def workout_finish(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        workout.notes = request.POST.get("notes", "")
        workout.duration_minutes = request.POST.get("duration") or None
        workout.save()
        messages.success(request, "Workout saved!")
        return redirect("tracker:workout_detail", pk=workout.pk)
    return render(request, "tracker/workout_finish.html", {"workout": workout})


@login_required
def workout_delete(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    workout.delete()
    messages.success(request, "Workout deleted.")
    return redirect("tracker:workout_list")


# ── Sets (HTMX) ─────────────────────────────────────────────────

@login_required
def set_add(request, we_pk):
    we = get_object_or_404(WorkoutExercise, pk=we_pk, workout__user=request.user)
    if request.method == "POST":
        reps = request.POST.get("reps") or None
        weight = request.POST.get("weight") or None
        if weight is not None:
            weight = float(weight)
            if request.user.profile.units == "imperial":
                weight = weight / 2.20462
            weight = round(weight, 2)
        rir = request.POST.get("rir") or None
        is_warmup = request.POST.get("is_warmup") == "on"
        max_set = we.sets.aggregate(m=Max("set_number"))["m"] or 0
        Set.objects.create(
            workout_exercise=we,
            set_number=max_set + 1,
            reps=reps,
            weight_kg=weight,
            rir=rir,
            is_warmup=is_warmup,
        )
    return redirect("tracker:workout_detail", pk=we.workout.pk)


@login_required
def set_delete(request, pk):
    s = get_object_or_404(Set, pk=pk, workout_exercise__workout__user=request.user)
    workout_pk = s.workout_exercise.workout.pk
    s.delete()
    return redirect("tracker:workout_detail", pk=workout_pk)


# ── Export ──────────────────────────────────────────────────────

@login_required
def export_data(request):
    if request.method == "POST":
        export_type = request.POST.get("type", "weight")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={export_type}.csv"
        writer = csv.writer(response)

        if export_type == "weight":
            writer.writerow(["Date", "Weight (kg)", "Notes"])
            for w in WeightLog.objects.filter(user=request.user).order_by("date"):
                writer.writerow([w.date, w.weight_kg, w.notes])
        elif export_type == "measurements":
            writer.writerow([
                "Date", "Waist (cm)", "Chest (cm)", "Left Arm (cm)", "Right Arm (cm)",
                "Left Thigh (cm)", "Right Thigh (cm)", "Hips (cm)",
                "Left Calf (cm)", "Right Calf (cm)", "Shoulders (cm)", "Neck (cm)", "Notes",
            ])
            for m in MeasurementLog.objects.filter(user=request.user).order_by("date"):
                writer.writerow([
                    m.date, m.waist_cm, m.chest_cm, m.left_arm_cm, m.right_arm_cm,
                    m.left_thigh_cm, m.right_thigh_cm, m.hips_cm,
                    m.left_calf_cm, m.right_calf_cm, m.shoulders_cm, m.neck_cm, m.notes,
                ])
        elif export_type == "workouts":
            writer.writerow(["Date", "Template", "Exercise", "Set", "Reps", "Weight (kg)", "Warmup"])
            for w in Workout.objects.filter(user=request.user).order_by("date"):
                for we in w.exercises.all():
                    for s in we.sets.all():
                        writer.writerow([
                            w.date, w.template.name if w.template else "",
                            we.exercise.name, s.set_number, s.reps, s.weight_kg, s.is_warmup,
                        ])
        return response
    return render(request, "tracker/export.html")
