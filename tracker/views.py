import base64
import csv
import json
import math
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Exists, Max, OuterRef, Prefetch, Q
from django.utils import timezone


def _safe_float(val, default=None):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=None):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, max_len=None):
    if val is None:
        return ""
    s = str(val).strip()
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s


def cleanup_empty_workouts(user):
    cutoff = timezone.now() - timedelta(hours=24)
    qs = Workout.objects.filter(
        user=user,
        duration_minutes__isnull=True,
        created_at__lt=cutoff,
    ).annotate(
        total_sets=Count("exercises__sets"),
    ).filter(total_sets=0)
    deleted, _ = qs.delete()
    return deleted


from .models import (
    ExerciseCategory, Exercise, WeightLog, MeasurementLog, BodyFatLog,
    WorkoutTemplate, WorkoutTemplateExercise, Workout, WorkoutExercise, Set,
    CardioLog,
)
from photos.models import ProgressPhoto
from .utils import convert_weight, convert_length, weight_unit, length_unit, convert_distance, distance_unit


def _weight_data(user, days=30):
    cutoff = date.today() - timedelta(days=days)
    logs = WeightLog.objects.filter(user=user, date__gte=cutoff).order_by("date")
    labels = [str(l.date) for l in logs]
    values = []
    for l in logs:
        v = round(float(l.weight_kg) * 2.20462, 1)
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
                v = round(float(val) * 0.393701, 1)
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


def _cardio_data(user, days=180):
    cutoff = date.today() - timedelta(days=days)
    logs = CardioLog.objects.filter(user=user, date__gte=cutoff).order_by("date")
    if not logs.exists():
        return "[]", "[]", False

    activity_groups = defaultdict(list)
    for log in logs:
        activity_groups[log.activity].append({
            "date": str(log.date),
            "duration": log.duration_minutes,
        })

    all_dates = sorted(set(str(log.date) for log in logs))
    colors = [
        "#3b82f6", "#ef4444", "#16a34a", "#9333ea", "#f97316",
        "#14b8a6", "#db2777", "#f59e0b", "#06b6d4", "#84cc16",
        "#8b5cf6", "#ec4899", "#0ea5e9", "#a855f7", "#e11d48",
    ]

    datasets = []
    for i, (activity, points) in enumerate(activity_groups.items()):
        pt_map = {p["date"]: p for p in points}
        data = []
        for d in all_dates:
            if d in pt_map:
                data.append(pt_map[d]["duration"])
            else:
                data.append(None)
        c = colors[i % len(colors)]
        datasets.append({
            "label": activity,
            "data": data,
            "borderColor": c,
            "backgroundColor": c + "33",
            "tension": 0.3,
            "spanGaps": False,
        })

    labels_json = json.dumps(all_dates)
    datasets_json = json.dumps(datasets)
    return labels_json, datasets_json, True


@login_required
def dashboard(request):
    cleanup_empty_workouts(request.user)
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
        weight_change = round(
            (float(last_weight.weight_kg) - float(week_ago_weight.weight_kg)) * 2.20462, 1
        )

    has_weight_data = bool(weight_labels)
    meas_labels, meas_datasets, has_meas_data = _measurement_data(request.user, 180)

    profile = getattr(request.user, "profile", None)
    bmi = None
    bmi_category = None
    goal_remaining_lbs = None
    goal_direction = None
    goal_reached = False
    if profile:
        if last_weight and profile.height_cm:
            height_m = float(profile.height_cm) / 100.0
            bmi_val = float(last_weight.weight_kg) / (height_m ** 2)
            bmi = round(bmi_val, 1)
            if bmi_val < 18.5:
                bmi_category = "Underweight"
            elif bmi_val < 25:
                bmi_category = "Normal"
            elif bmi_val < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"
        if last_weight and profile.goal_weight_kg:
            remaining = float(profile.goal_weight_kg) - float(last_weight.weight_kg)
            goal_remaining_lbs = round(abs(remaining) * 2.20462, 1)
            goal_direction = "gain" if remaining > 0 else "lose"
            goal_reached = abs(remaining) < 0.1

    body_fat_pct = None
    body_fat_method = None
    body_fat_navy_pct = None
    fat_mass_display = None
    lean_mass_display = None
    bf_goal_remaining = None
    bf_goal_direction = None
    bf_goal_reached = False
    if profile and last_weight:
        # Latest Navy-calculated body fat
        latest_meas = MeasurementLog.objects.filter(
            user=request.user, waist_cm__isnull=False, neck_cm__isnull=False
        ).order_by("-date").first()
        navy_pct = None
        if latest_meas and profile.height_cm:
            waist = float(latest_meas.waist_cm)
            neck = float(latest_meas.neck_cm)
            height_cm = float(profile.height_cm)
            if waist > neck:
                if profile.sex == "female":
                    hips = float(latest_meas.hips_cm) if latest_meas.hips_cm else None
                    if hips:
                        bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height_cm) - 78.387
                    else:
                        bf = None
                else:
                    bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height_cm) + 36.76
                if bf is not None and 3 < bf < 70:
                    navy_pct = round(bf, 1)

        # Latest direct BodyFatLog entry
        latest_direct = BodyFatLog.objects.filter(user=request.user).order_by("-date").first()

        # Pick the most recent by date
        navy_date = latest_meas.date if latest_meas else None
        direct_date = latest_direct.date if latest_direct else None
        latest_entry = None
        if direct_date and (not navy_date or direct_date >= navy_date):
            latest_entry = latest_direct
        elif navy_pct:
            latest_entry = None  # use navy

        if latest_direct and direct_date and (not navy_date or direct_date >= navy_date):
            body_fat_pct = latest_direct.body_fat_pct
            body_fat_method = latest_direct.method
        elif navy_pct:
            body_fat_pct = navy_pct
            body_fat_method = "navy"
        else:
            body_fat_pct = None
            body_fat_method = None

        body_fat_navy_pct = navy_pct

        if body_fat_pct:
            weight_kg = float(last_weight.weight_kg)
            fat_kg = weight_kg * body_fat_pct / 100.0
            lean_kg = weight_kg - fat_kg
            fat_mass_display = round(fat_kg * 2.20462, 1)
            lean_mass_display = round(lean_kg * 2.20462, 1)

        if body_fat_pct and profile.goal_body_fat_pct:
            bf_remaining = float(profile.goal_body_fat_pct) - body_fat_pct
            bf_goal_remaining = round(abs(bf_remaining), 1)
            bf_goal_direction = "gain" if bf_remaining > 0 else "lose"
            bf_goal_reached = abs(bf_remaining) < 0.1
        else:
            bf_goal_reached = False

    exercise_progress = defaultdict(list)
    wes = WorkoutExercise.objects.filter(
        workout__user=request.user,
    ).select_related(
        "exercise", "workout"
    ).prefetch_related("sets").order_by("workout__date")
    for we in wes:
        working = [s for s in we.sets.all() if not s.is_warmup and s.weight_kg and float(s.weight_kg) > 0]
        if not working:
            continue
        heaviest = max(working, key=lambda s: float(s.weight_kg))
        w = round(float(heaviest.weight_kg) * 2.20462, 1)
        exercise_progress[we.exercise.name].append({
            "date": str(we.workout.date),
            "weight": w,
            "reps": heaviest.reps,
        })

    if exercise_progress:
        all_dates = sorted(set(
            d["date"]
            for points in exercise_progress.values()
            for d in points
        ))
        colors = [
            "#3b82f6", "#ef4444", "#16a34a", "#9333ea", "#f97316",
            "#14b8a6", "#db2777", "#f59e0b", "#06b6d4", "#84cc16",
            "#8b5cf6", "#ec4899", "#0ea5e9", "#a855f7", "#e11d48",
        ]
        exercise_datasets = []
        for i, (name, points) in enumerate(exercise_progress.items()):
            pt_map = {p["date"]: p for p in points}
            data = []
            reps_data = []
            for d in all_dates:
                if d in pt_map:
                    data.append(pt_map[d]["weight"])
                    reps_data.append(pt_map[d]["reps"])
                else:
                    data.append(None)
                    reps_data.append(None)
            c = colors[i % len(colors)]
            exercise_datasets.append({
                "label": name,
                "data": data,
                "reps": reps_data,
                "borderColor": c,
                "backgroundColor": c + "33",
                "tension": 0.3,
                "spanGaps": True,
            })
        exercise_labels = json.dumps(all_dates)
        exercise_json = json.dumps(exercise_datasets)
    else:
        exercise_labels = "[]"
        exercise_json = "[]"

    bf_labels = "[]"
    bf_values = "[]"
    bf_styles = "[]"
    bf_method_labels = "[]"
    has_bf_data = False
    bf_goal_val = profile.goal_body_fat_pct if profile and profile.goal_body_fat_pct else None
    if profile and profile.height_cm and weight_labels:
        cutoff = date.today() - timedelta(days=180)
        meas_logs = list(MeasurementLog.objects.filter(
            user=request.user, date__gte=cutoff, waist_cm__isnull=False, neck_cm__isnull=False
        ).order_by("date"))
        # Build a map: measurement_date -> body_fat_value (Navy calc)
        bf_map = {}
        height_cm = float(profile.height_cm)
        for m in meas_logs:
            waist = float(m.waist_cm)
            neck = float(m.neck_cm)
            if waist <= neck:
                continue
            if profile.sex == "female":
                hips = float(m.hips_cm) if m.hips_cm else None
                if not hips:
                    continue
                bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height_cm) - 78.387
            else:
                bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height_cm) + 36.76
            if bf is not None and 3 < bf < 70:
                bf_map[str(m.date)] = round(bf, 1)

        # Build direct BodyFatLog entries map (most recent creation wins for dup dates)
        direct_logs = BodyFatLog.objects.filter(
            user=request.user, date__gte=cutoff
        ).order_by("date", "-created_at")
        direct_bf = {}
        for l in direct_logs:
            direct_bf[str(l.date)] = {"value": l.body_fat_pct, "method": l.method}

        # Only proceed if we have body fat data from either source
        if bf_map or direct_bf:
            all_sources = list(bf_map.keys()) + list(direct_bf.keys())
            if not bf_map:
                all_sources = list(direct_bf.keys())

            # Merge weight and BF dates into one sorted label list
            all_dates_set = sorted(set(weight_labels + all_sources))

            # Rebuild weight data with gaps for non-weight dates
            weight_by_date = {wl_date: wv for wl_date, wv in zip(weight_labels, weight_values)}
            merged_weight = []
            for d in all_dates_set:
                merged_weight.append(weight_by_date.get(d))

            # Build BF data aligned to merged dates
            # Priority: direct entry > Navy calculation (carry-forward)
            sorted_navy_dates = sorted(bf_map.keys())
            merged_bf = []
            merged_styles = []
            merged_radii = []
            merged_methods = []
            for d in all_dates_set:
                if d in direct_bf:
                    merged_bf.append(direct_bf[d]["value"])
                    merged_styles.append("triangle")
                    merged_radii.append(6)
                    merged_methods.append(direct_bf[d]["method"])
                else:
                    closest = None
                    for nd in sorted_navy_dates:
                        if nd <= d:
                            closest = nd
                    if closest:
                        merged_bf.append(bf_map[closest])
                        merged_styles.append("circle")
                        merged_radii.append(2.5)
                        merged_methods.append("navy")
                    else:
                        merged_bf.append(None)
                        merged_styles.append("circle")
                        merged_radii.append(0)
                        merged_methods.append("navy")

            has_bf_data = any(v is not None for v in merged_bf)
            weight_labels = all_dates_set
            weight_values = merged_weight
            bf_labels = json.dumps(all_dates_set)
            bf_values = json.dumps(merged_bf)
            bf_styles = json.dumps(merged_styles)
            bf_radii = json.dumps(merged_radii)
            bf_method_labels = json.dumps(merged_methods)

    recent_cardio = CardioLog.objects.filter(user=request.user).order_by("-date")[:5]
    cardio_labels, cardio_datasets, has_cardio_data = _cardio_data(request.user, 180)

    ctx = {
        "recent_weight": recent_weight,
        "recent_measurements": recent_measurements,
        "recent_workouts": recent_workouts,
        "recent_cardio": recent_cardio,
        "cardio_labels": cardio_labels,
        "cardio_datasets": cardio_datasets,
        "has_cardio_data": has_cardio_data,
        "body_fat_pct": body_fat_pct,
        "fat_mass_display": fat_mass_display,
        "lean_mass_display": lean_mass_display,
        "weight_labels": json.dumps(weight_labels) if has_weight_data else "[]",
        "weight_values": json.dumps(weight_values) if has_weight_data else "[]",
        "has_weight_data": has_weight_data,
        "last_weight": last_weight,
        "weight_change": weight_change,
        "meas_labels": meas_labels,
        "meas_datasets": meas_datasets,
        "has_meas_data": has_meas_data,
        "bf_labels": bf_labels,
        "bf_values": bf_values,
        "bf_styles": bf_styles,
        "bf_radii": bf_radii,
        "bf_method_labels": bf_method_labels,
        "has_bf_data": has_bf_data,
        "body_fat_method": body_fat_method,
        "body_fat_navy_pct": body_fat_navy_pct,
        "bf_goal_val": bf_goal_val,
        "wu": weight_unit(request.user),
        "lu": length_unit(request.user),
        "exercise_labels": exercise_labels,
        "exercise_datasets": exercise_json,
        "has_exercise_progress": bool(exercise_progress),
        "bmi": bmi,
        "bmi_category": bmi_category,
        "goal_remaining_lbs": goal_remaining_lbs,
        "goal_direction": goal_direction,
        "goal_reached": goal_reached,
        "bf_goal_remaining": bf_goal_remaining,
        "bf_goal_direction": bf_goal_direction,
        "bf_goal_reached": bf_goal_reached,
        "goal_body_fat_pct": profile.goal_body_fat_pct if profile else None,
    }
    return render(request, "tracker/dashboard.html", ctx)


# ── Weight ──────────────────────────────────────────────────────

@login_required
def weight_add(request):
    if request.method == "POST":
        date_val = request.POST.get("date", date.today())
        weight_lbs = request.POST.get("weight")
        notes_val = _safe_str(request.POST.get("notes", ""))
        weight_kg = _safe_float(weight_lbs)
        if weight_kg is not None:
            weight_kg = round(weight_kg / 2.20462, 2)
        if weight_kg is not None:
            WeightLog.objects.update_or_create(
                user=request.user,
                date=date_val,
                defaults={"weight_kg": round(weight_kg, 2), "notes": notes_val},
            )
            messages.success(request, "Weight logged!")
            return redirect("tracker:weight_list")
    return render(request, "tracker/weight_form.html")


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


# ── Cardio ──────────────────────────────────────────────────────


@login_required
def cardio_add(request):
    if request.method == "POST":
        date_val = request.POST.get("date", date.today())
        activity = _safe_str(request.POST.get("activity"), max_len=100)
        duration = request.POST.get("duration")
        dist_mi = request.POST.get("distance")
        notes_val = _safe_str(request.POST.get("notes", ""))
        if activity in ("Running", "Cycling") and not dist_mi:
            messages.error(request, "Distance is required for Running and Cycling.")
        elif activity and duration:
            duration_int = _safe_int(duration)
            if duration_int and duration_int > 0:
                dist_km_raw = _safe_float(dist_mi)
                dist_km = round(dist_km_raw / 0.621371, 2) if dist_km_raw else None
                CardioLog.objects.create(
                    user=request.user,
                    date=date_val,
                    activity=activity,
                    duration_minutes=duration_int,
                    distance_km=dist_km,
                    notes=notes_val,
                )
                messages.success(request, "Cardio logged!")
                return redirect("tracker:cardio_list")
    return render(request, "tracker/cardio_form.html")


@login_required
def cardio_list(request):
    logs = CardioLog.objects.filter(user=request.user).order_by("-date")
    return render(request, "tracker/cardio_list.html", {
        "logs": logs,
        "du": distance_unit(request.user),
    })


@login_required
def cardio_delete(request, pk):
    log = get_object_or_404(CardioLog, pk=pk, user=request.user)
    log.delete()
    messages.success(request, "Cardio entry deleted.")
    return redirect("tracker:cardio_list")


# ── Body Fat ────────────────────────────────────────────────────

@login_required
def body_fat_list(request):
    logs = BodyFatLog.objects.filter(user=request.user).order_by("-date")
    return render(request, "tracker/body_fat_list.html", {"logs": logs})


@login_required
def body_fat_add(request):
    if request.method == "POST":
        date_val = request.POST.get("date", date.today())
        bf = _safe_float(request.POST.get("body_fat_pct"))
        method = request.POST.get("method", "manual")
        notes_val = _safe_str(request.POST.get("notes", ""))
        if bf is not None and 1 < bf < 70:
            BodyFatLog.objects.create(
                user=request.user,
                date=date_val,
                body_fat_pct=round(bf, 1),
                method=method,
                notes=notes_val,
            )
            messages.success(request, "Body fat entry saved!")
            return redirect("tracker:body_fat_list")
        else:
            messages.error(request, "Please enter a valid body fat percentage (1–70).")
    return render(request, "tracker/body_fat_form.html")


@login_required
def body_fat_delete(request, pk):
    log = get_object_or_404(BodyFatLog, pk=pk, user=request.user)
    log.delete()
    messages.success(request, "Body fat entry deleted.")
    return redirect("tracker:body_fat_list")


# ── Measurements ────────────────────────────────────────────────

@login_required
def measurement_add(request):
    if request.method == "POST":
        is_imperial = getattr(request.user.profile, "units", "imperial") == "imperial"
        data = {k: request.POST.get(k) or None for k in [
            "waist_cm", "chest_cm", "left_arm_cm", "right_arm_cm",
            "left_thigh_cm", "right_thigh_cm", "hips_cm",
            "left_calf_cm", "right_calf_cm", "shoulders_cm", "neck_cm",
        ]}
        for k in data:
            raw = _safe_float(data[k])
            if raw is not None:
                if is_imperial:
                    data[k] = round(raw * 2.54, 1)
                else:
                    data[k] = round(raw, 1)
            else:
                data[k] = None

        MeasurementLog.objects.update_or_create(
            user=request.user,
            date=request.POST.get("date", date.today()),
            defaults={**data, "notes": request.POST.get("notes", "")},
        )
        messages.success(request, "Measurements saved!")
        return redirect("tracker:measurement_list")
    return render(request, "tracker/measurement_form.html")


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


# ── Exercise Categories ─────────────────────────────────────────

@login_required
def category_list(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            name = _safe_str(request.POST.get("name"), max_len=100)
            if name:
                ExerciseCategory.objects.get_or_create(user=request.user, name=name)
                messages.success(request, f"Category '{name}' created!")
        elif action == "rename":
            pk = request.POST.get("pk")
            name = _safe_str(request.POST.get("name"), max_len=100)
            if pk and name:
                cat = get_object_or_404(ExerciseCategory, pk=pk, user=request.user)
                cat.name = name
                cat.save()
                messages.success(request, "Category renamed!")
        elif action == "delete":
            pk = request.POST.get("pk")
            if pk:
                cat = get_object_or_404(ExerciseCategory, pk=pk, user=request.user)
                cat.delete()
                messages.success(request, "Category deleted.")
        return redirect("tracker:category_list")
    categories = ExerciseCategory.objects.filter(user=request.user).order_by("name")
    return render(request, "tracker/category_list.html", {"categories": categories})


# ── Exercises ───────────────────────────────────────────────────

@login_required
def exercise_list(request):
    exercises = Exercise.objects.filter(
        Q(user=request.user) | Q(user=None) | Q(is_public=True)
    ).prefetch_related("categories").order_by("name")
    return render(request, "tracker/exercise_list.html", {
        "exercises": exercises,
    })


@login_required
def muscle_list(request):
    visible_ex = Q(user=request.user) | Q(user=None) | Q(is_public=True)
    categories = ExerciseCategory.objects.filter(
        user__in=[request.user, None]
    ).distinct().prefetch_related(
        Prefetch("exercises", queryset=Exercise.objects.filter(
            visible_ex
        ), to_attr="cat_exercises")
    ).order_by("name")
    all_exercises = Exercise.objects.filter(
        visible_ex
    ).prefetch_related("categories").order_by("name")
    uncategorized = [ex for ex in all_exercises if not ex.categories.all()]
    return render(request, "tracker/muscle_list.html", {
        "categories": categories,
        "uncategorized": uncategorized,
    })


@login_required
def exercise_add(request):
    if request.method == "POST":
        name = _safe_str(request.POST.get("name"), max_len=200)
        category_ids = request.POST.getlist("categories")
        new_category_name = _safe_str(request.POST.get("new_category", ""), max_len=100)
        notes = _safe_str(request.POST.get("notes", ""))

        cats = []
        for cid in category_ids:
            cat = ExerciseCategory.objects.filter(
                pk=cid, user__in=[request.user, None]
            ).first()
            if cat:
                cats.append(cat)
        if new_category_name:
            cat, _ = ExerciseCategory.objects.get_or_create(
                user=request.user, name=new_category_name,
            )
            cats.append(cat)

        is_public = request.POST.get("is_public") == "on"
        if name:
            exercise, created = Exercise.objects.get_or_create(
                user=request.user, name=name,
                defaults={"notes": notes, "is_public": is_public},
            )
            if not created:
                exercise.notes = notes
                exercise.is_public = is_public
                exercise.save()
            if cats:
                exercise.categories.set(cats)
            messages.success(request, f"Exercise '{name}' added!")
            return redirect("tracker:exercise_list")
    return render(request, "tracker/exercise_form.html", {
        "categories": ExerciseCategory.objects.filter(
            user__in=[request.user, None]
        ).distinct(),
    })


@login_required
def exercise_edit(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    if request.method == "POST":
        exercise.name = _safe_str(request.POST.get("name", exercise.name), max_len=200) or exercise.name
        exercise.notes = _safe_str(request.POST.get("notes", ""))
        exercise.is_public = request.POST.get("is_public") == "on"
        exercise.save()

        category_ids = request.POST.getlist("categories")
        new_category_name = request.POST.get("new_category", "").strip()
        cats = []
        for cid in category_ids:
            cat = ExerciseCategory.objects.filter(
                pk=cid, user__in=[request.user, None]
            ).first()
            if cat:
                cats.append(cat)
        if new_category_name:
            cat, _ = ExerciseCategory.objects.get_or_create(
                user=request.user, name=new_category_name,
            )
            cats.append(cat)
        exercise.categories.set(cats)
        messages.success(request, f"Exercise '{exercise.name}' updated!")
        return redirect("tracker:exercise_list")

    categories = ExerciseCategory.objects.filter(
        user__in=[request.user, None]
    ).distinct()
    selected_ids = list(exercise.categories.values_list("pk", flat=True))
    return render(request, "tracker/exercise_form.html", {
        "exercise": exercise,
        "categories": categories,
        "selected_ids": selected_ids,
        "editing": True,
    })


@login_required
def exercise_delete(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, user=request.user)
    exercise.delete()
    messages.success(request, "Exercise deleted.")
    return redirect("tracker:exercise_list")


# ── Workout Templates ──────────────────────────────────────────

def _build_exercise_data(user, existing_exercises=None):
    base_qs = Exercise.objects.filter(
        Q(user=user) | Q(user=None) | Q(is_public=True)
    ).prefetch_related("categories")
    if existing_exercises is not None:
        existing = {te.exercise_id: te for te in existing_exercises}
        data = []
        for te in existing_exercises:
            ex = te.exercise
            data.append({
                "exercise": ex,
                "checked": True,
                "target_sets": te.target_sets,
                "target_reps_min": te.target_reps_min,
                "target_reps_max": te.target_reps_max,
            })
        checked_ids = set(existing.keys())
        for ex in base_qs.order_by("name"):
            if ex.pk not in checked_ids:
                data.append({
                    "exercise": ex,
                    "checked": False,
                    "target_sets": None,
                    "target_reps_min": None,
                    "target_reps_max": None,
                })
        return data

    exercises = base_qs.order_by("name")
    data = []
    for ex in exercises:
        data.append({
            "exercise": ex,
            "checked": False,
            "target_sets": None,
            "target_reps_min": None,
            "target_reps_max": None,
        })
    return data


def _save_exercise_targets(tpl, exercise_ids, request):
    for i, eid in enumerate(exercise_ids):
        if not eid:
            continue
        exercise = Exercise.objects.filter(pk=eid).first()
        if not exercise:
            continue
        target_sets = _safe_int(request.POST.get(f"target_sets_{eid}"))
        target_reps_min = _safe_int(request.POST.get(f"target_reps_min_{eid}"))
        target_reps_max = _safe_int(request.POST.get(f"target_reps_max_{eid}"))
        WorkoutTemplateExercise.objects.create(
            template=tpl,
            exercise=exercise,
            order=i,
            target_sets=target_sets,
            target_reps_min=target_reps_min,
            target_reps_max=target_reps_max,
        )


@login_required
def template_list(request):
    templates = WorkoutTemplate.objects.filter(
        Q(user=request.user) | Q(is_public=True)
    ).order_by("name")
    return render(request, "tracker/template_list.html", {"templates": templates})


@login_required
def template_add(request):
    if request.method == "POST":
        name = _safe_str(request.POST.get("name"), max_len=200)
        description = _safe_str(request.POST.get("description", ""))
        exercise_ids = request.POST.getlist("exercises")
        is_public = request.POST.get("is_public") == "on"
        if name:
            tpl = WorkoutTemplate.objects.create(
                user=request.user, name=name, description=description,
                is_public=is_public,
            )
            _save_exercise_targets(tpl, exercise_ids, request)
            messages.success(request, f"Template '{name}' created!")
            return redirect("tracker:template_list")
    exercise_data = _build_exercise_data(request.user)
    return render(request, "tracker/template_form.html", {
        "exercise_data": exercise_data,
        "wu": "lbs",
        "template_is_public": False,
    })


@login_required
def template_edit(request, pk):
    tpl = get_object_or_404(WorkoutTemplate, pk=pk, user=request.user)
    if request.method == "POST":
        tpl.name = _safe_str(request.POST.get("name", tpl.name), max_len=200) or tpl.name
        tpl.description = _safe_str(request.POST.get("description", ""))
        tpl.is_public = request.POST.get("is_public") == "on"
        tpl.save()
        tpl.exercises.all().delete()
        exercise_ids = request.POST.getlist("exercises")
        _save_exercise_targets(tpl, exercise_ids, request)
        messages.success(request, f"Template '{tpl.name}' updated!")
        return redirect("tracker:template_detail", pk=tpl.pk)
    existing_exercises = list(tpl.exercises.select_related("exercise").all())
    exercise_data = _build_exercise_data(request.user, existing_exercises)
    return render(request, "tracker/template_form.html", {
        "exercise_data": exercise_data,
        "template_name": tpl.name,
        "template_description": tpl.description,
        "template_is_public": tpl.is_public,
        "editing": True,
        "wu": "lbs",
    })


@login_required
def template_detail(request, pk):
    tpl = get_object_or_404(WorkoutTemplate, pk=pk)
    if tpl.user != request.user and not tpl.is_public:
        raise Http404()
    ctx = {
        "template": tpl,
        "is_owner": tpl.user == request.user,
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
    cleanup_empty_workouts(request.user)
    tpl = get_object_or_404(WorkoutTemplate, pk=pk)
    if tpl.user != request.user and not tpl.is_public:
        raise Http404()
    workout_date = request.GET.get("date") or date.today()
    workout = Workout.objects.create(user=request.user, date=workout_date, template=tpl)
    for te in tpl.exercises.select_related("exercise").all():
        WorkoutExercise.objects.create(
            workout=workout, exercise=te.exercise, order=te.order,
            target_sets=te.target_sets,
            target_reps_min=te.target_reps_min,
            target_reps_max=te.target_reps_max,
        )
    return redirect("tracker:workout_detail", pk=workout.pk)


# ── Workouts ───────────────────────────────────────────────────

@login_required
def workout_list(request):
    cleanup_empty_workouts(request.user)
    workouts = Workout.objects.filter(user=request.user).order_by("-date", "-created_at")
    return render(request, "tracker/workout_list.html", {"workouts": workouts})


@login_required
def workout_add(request):
    templates = WorkoutTemplate.objects.filter(
        Q(user=request.user) | Q(is_public=True)
    ).order_by("name")
    if request.method == "POST":
        cleanup_empty_workouts(request.user)
        template_id = request.POST.get("template")
        workout_date = request.POST.get("date", date.today())
        if template_id:
            return redirect(f"{reverse('tracker:template_start_workout', kwargs={'pk': template_id})}?date={workout_date}")
        else:
            workout = Workout.objects.create(user=request.user, date=workout_date)
            return redirect("tracker:workout_detail", pk=workout.pk)
    return render(request, "tracker/workout_form.html", {
        "templates": templates,
    })


@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    exercises = workout.exercises.select_related("exercise").prefetch_related("sets").all()
    all_exercises = Exercise.objects.filter(
        Q(user=request.user) | Q(user=None) | Q(is_public=True)
    ).order_by("name")

    for we in exercises:
        we.weight_suggestion = None
        we.completed_goal = False

        working_sets = [s for s in we.sets.all() if not s.is_warmup and s.reps is not None]
        if (
            we.target_reps_max
            and we.target_sets
            and len(working_sets) >= we.target_sets
            and all(s.reps >= we.target_reps_max for s in working_sets[:we.target_sets])
        ):
            we.completed_goal = True

        current_working = [s for s in we.sets.all() if not s.is_warmup and s.weight_kg]
        if current_working:
            last_set = current_working[-1]
            we.weight_suggestion = {
                "kg": float(last_set.weight_kg),
                "diff": "from last set",
            }
        else:
            has_sets = Set.objects.filter(workout_exercise=OuterRef("pk"))
            prev_we = WorkoutExercise.objects.filter(
                exercise=we.exercise,
                workout__user=request.user,
            ).exclude(
                workout=workout
            ).annotate(
                has_sets=Exists(has_sets)
            ).filter(
                has_sets=True
            ).select_related("workout").prefetch_related("sets").order_by(
                "-workout__date", "-workout__created_at"
            ).first()

            if prev_we and we.target_reps_max and we.target_sets:
                prev_working = [s for s in prev_we.sets.all() if not s.is_warmup and s.reps is not None and s.weight_kg]
                first_set = prev_working[0] if prev_working else None
                if first_set:
                    prev_weight = float(first_set.weight_kg)
                    increase_lbs = 5
                    increase_kg = round(increase_lbs / 2.20462, 2)
                    all_at_max = (
                        len(prev_working) >= we.target_sets
                        and all(s.reps >= we.target_reps_max for s in prev_working[:we.target_sets])
                    )
                    if all_at_max:
                        suggested = prev_weight + increase_kg
                        label_diff = f"+{increase_lbs} lbs"
                    else:
                        suggested = prev_weight
                        label_diff = "same"

                    we.weight_suggestion = {
                        "kg": round(suggested, 2),
                        "diff": label_diff,
                    }

    return render(request, "tracker/workout_detail.html", {
        "workout": workout,
        "workout_exercises": exercises,
        "all_exercises": all_exercises,
        "wu": weight_unit(request.user),
        "lu": length_unit(request.user),
        "convert_weight": convert_weight,
    })


@login_required
def workout_exercise_add(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        exercise_id = request.POST.get("exercise")
        if exercise_id:
            exercise = get_object_or_404(
                Exercise.objects.filter(
                    Q(user=request.user) | Q(user=None) | Q(is_public=True)
                ), pk=exercise_id)
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
def workout_reorder(request, pk):
    if request.method == "POST":
        workout = get_object_or_404(Workout, pk=pk, user=request.user)
        exercise_ids = request.POST.getlist("exercise_ids")
        for i, eid in enumerate(exercise_ids):
            WorkoutExercise.objects.filter(pk=eid, workout=workout).update(order=i)
        return HttpResponse("ok")
    return HttpResponseBadRequest()


@login_required
def workout_finish(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == "POST":
        workout.notes = _safe_str(request.POST.get("notes", ""))
        workout.duration_minutes = _safe_int(request.POST.get("duration"))
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
        reps = _safe_int(request.POST.get("reps"))
        weight_raw = _safe_float(request.POST.get("weight"))
        weight = round(weight_raw / 2.20462, 2) if weight_raw else None
        is_warmup = request.POST.get("is_warmup") == "on"
        max_set = we.sets.aggregate(m=Max("set_number"))["m"] or 0
        Set.objects.create(
            workout_exercise=we,
            set_number=max_set + 1,
            reps=reps,
            weight_kg=weight,
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
        elif export_type == "cardio":
            writer.writerow(["Date", "Activity", "Duration (min)", "Distance (km)", "Notes"])
            for c in CardioLog.objects.filter(user=request.user).order_by("date"):
                writer.writerow([c.date, c.activity, c.duration_minutes, c.distance_km, c.notes])
        elif export_type == "bodyfat":
            writer.writerow(["Date", "Body Fat %", "Method", "Notes"])
            for b in BodyFatLog.objects.filter(user=request.user).order_by("date"):
                writer.writerow([b.date, b.body_fat_pct, b.method, b.notes])
        return response
    return render(request, "tracker/import_export.html")


EXPORT_VERSION = 1


@login_required
def export_all(request):
    user = request.user
    logs_qs = WeightLog.objects.filter(user=user).order_by("date")
    meas_qs = MeasurementLog.objects.filter(user=user).order_by("date")
    cardio_qs = CardioLog.objects.filter(user=user).order_by("date")
    cats_qs = ExerciseCategory.objects.filter(user=user).order_by("name")
    exercises_qs = Exercise.objects.filter(user=user).prefetch_related("categories").order_by("name")
    templates_qs = WorkoutTemplate.objects.filter(user=user).prefetch_related(
        "exercises__exercise"
    ).order_by("name")
    workouts_qs = Workout.objects.filter(user=user).prefetch_related(
        "exercises__exercise", "exercises__sets"
    ).order_by("date")
    photos_qs = ProgressPhoto.objects.filter(user=user).order_by("date")

    profile = getattr(user, "profile", None)
    profile_data = None
    if profile:
        profile_data = {
            "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
            "height_cm": profile.height_cm,
            "goal_weight_kg": profile.goal_weight_kg,
            "goal_body_fat_pct": profile.goal_body_fat_pct,
            "sex": profile.sex,
            "units": profile.units,
            "theme": profile.theme,
            "nav_color": profile.nav_color,
        }

    data = {
        "version": EXPORT_VERSION,
        "exported_at": date.today().isoformat(),
        "profile": profile_data,
        "exercise_categories": [{"name": c.name} for c in cats_qs],
        "exercises": [
            {
                "name": e.name,
                "categories": [c.name for c in e.categories.all()],
                "notes": e.notes,
                "is_public": e.is_public,
            }
            for e in exercises_qs
        ],
        "weight_logs": [
            {"date": str(w.date), "weight_kg": float(w.weight_kg), "notes": w.notes}
            for w in logs_qs
        ],
        "measurements": [
            {
                "date": str(m.date),
                "waist_cm": float(m.waist_cm) if m.waist_cm else None,
                "chest_cm": float(m.chest_cm) if m.chest_cm else None,
                "left_arm_cm": float(m.left_arm_cm) if m.left_arm_cm else None,
                "right_arm_cm": float(m.right_arm_cm) if m.right_arm_cm else None,
                "left_thigh_cm": float(m.left_thigh_cm) if m.left_thigh_cm else None,
                "right_thigh_cm": float(m.right_thigh_cm) if m.right_thigh_cm else None,
                "hips_cm": float(m.hips_cm) if m.hips_cm else None,
                "left_calf_cm": float(m.left_calf_cm) if m.left_calf_cm else None,
                "right_calf_cm": float(m.right_calf_cm) if m.right_calf_cm else None,
                "shoulders_cm": float(m.shoulders_cm) if m.shoulders_cm else None,
                "neck_cm": float(m.neck_cm) if m.neck_cm else None,
                "notes": m.notes,
            }
            for m in meas_qs
        ],
        "workout_templates": [
            {
                "name": t.name,
                "description": t.description,
                "is_public": t.is_public,
                "exercises": [
                    {
                        "exercise_name": te.exercise.name,
                        "order": te.order,
                        "target_sets": te.target_sets,
                        "target_reps_min": te.target_reps_min,
                        "target_reps_max": te.target_reps_max,
                    }
                    for te in t.exercises.all()
                ],
            }
            for t in templates_qs
        ],
        "workouts": [
            {
                "date": str(w.date),
                "template_name": w.template.name if w.template else None,
                "duration_minutes": w.duration_minutes,
                "notes": w.notes,
                "exercises": [
                    {
                        "exercise_name": we.exercise.name,
                        "order": we.order,
                        "sets": [
                            {
                                "set_number": s.set_number,
                                "reps": s.reps,
                                "weight_kg": float(s.weight_kg) if s.weight_kg else None,
                                "is_warmup": s.is_warmup,
                            }
                            for s in we.sets.all()
                        ],
                    }
                    for we in w.exercises.all()
                ],
            }
            for w in workouts_qs
        ],
        "cardio_logs": [
            {
                "date": str(c.date),
                "activity": c.activity,
                "duration_minutes": c.duration_minutes,
                "distance_km": float(c.distance_km) if c.distance_km else None,
                "notes": c.notes,
            }
            for c in cardio_qs
        ],
        "body_fat_logs": [
            {
                "date": str(b.date),
                "body_fat_pct": b.body_fat_pct,
                "method": b.method,
                "notes": b.notes,
            }
            for b in BodyFatLog.objects.filter(user=user).order_by("date")
        ],
        "photos": [],
    }

    for p in photos_qs:
        try:
            raw = p.image.read()
            encoded = base64.b64encode(raw).decode("utf-8")
            data["photos"].append({
                "date": str(p.date),
                "body_part": p.body_part,
                "image_filename": p.image.name.split("/")[-1],
                "image_base64": encoded,
                "notes": p.notes,
            })
        except Exception:
            data["photos"].append({
                "date": str(p.date),
                "body_part": p.body_part,
                "image_filename": p.image.name.split("/")[-1],
                "image_base64": None,
                "notes": p.notes,
            })

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("fitness_data.json", json.dumps(data, indent=2))
    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="fitness_data_{date.today()}.zip"'
    return response


@login_required
def import_data(request):
    results = {"created": defaultdict(int), "updated": defaultdict(int), "skipped": defaultdict(int), "errors": []}
    profile = getattr(request.user, "profile", None)

    if request.method == "POST":
        uploaded = request.FILES.get("import_file")
        if not uploaded:
            messages.error(request, "No file uploaded.")
            return redirect("tracker:import_export")

        try:
            raw = uploaded.read()
            if uploaded.name.endswith(".zip"):
                with zipfile.ZipFile(BytesIO(raw)) as zf:
                    names = [n for n in zf.namelist() if n.endswith(".json")]
                    if not names:
                        messages.error(request, "ZIP file contains no JSON files.")
                        return redirect("tracker:import_export")
                    raw = zf.read(names[0])
            payload = json.loads(raw.decode("utf-8"))
        except (zipfile.BadZipfile, json.JSONDecodeError, UnicodeDecodeError) as e:
            messages.error(request, f"Invalid file: {e}")
            return redirect("tracker:import_export")

        if not isinstance(payload, dict) or payload.get("version") != EXPORT_VERSION:
            messages.error(
                request,
                f"Unsupported file version. Expected v{EXPORT_VERSION}.",
            )
            return redirect("tracker:import_export")

        data = payload.get("data") or payload  # support both flat and nested

        # 1. Profile
        pd = data.get("profile")
        if pd and profile:
            changed = False
            for field in ("date_of_birth", "height_cm", "goal_weight_kg", "goal_body_fat_pct", "sex", "units", "theme", "nav_color"):
                val = pd.get(field)
                if val is not None and getattr(profile, field) != val:
                    setattr(profile, field, val)
                    changed = True
            if pd.get("date_of_birth") is None and profile.date_of_birth:
                profile.date_of_birth = None
                changed = True
            if changed:
                profile.save()
                results["updated"]["profile"] += 1
            else:
                results["skipped"]["profile"] += 1

        # 2. Exercise Categories
        for cat_data in data.get("exercise_categories", []):
            name = cat_data.get("name", "").strip()
            if not name:
                continue
            _, created = ExerciseCategory.objects.get_or_create(
                user=request.user, name=name
            )
            if created:
                results["created"]["categories"] += 1
            else:
                results["skipped"]["categories"] += 1

        # 3. Exercises
        name_to_cats = {c.name: c for c in ExerciseCategory.objects.filter(user=request.user)}
        for ex_data in data.get("exercises", []):
            name = ex_data.get("name", "").strip()
            if not name:
                continue
            ex, created = Exercise.objects.get_or_create(
                user=request.user, name=name,
                defaults={
                    "notes": ex_data.get("notes", ""),
                    "is_public": ex_data.get("is_public", False),
                },
            )
            if created:
                cat_names = ex_data.get("categories", [])
                if cat_names:
                    matched = [name_to_cats[n] for n in cat_names if n in name_to_cats]
                    if matched:
                        ex.categories.set(matched)
                results["created"]["exercises"] += 1
            else:
                results["skipped"]["exercises"] += 1

        # 4. Weight Logs
        for wl in data.get("weight_logs", []):
            wl_date = wl.get("date")
            if not wl_date:
                continue
            _, created = WeightLog.objects.get_or_create(
                user=request.user, date=wl_date,
                defaults={
                    "weight_kg": wl.get("weight_kg", 0),
                    "notes": wl.get("notes", ""),
                },
            )
            if created:
                results["created"]["weight_logs"] += 1
            else:
                results["skipped"]["weight_logs"] += 1

        # 5. Measurements
        for m in data.get("measurements", []):
            m_date = m.get("date")
            if not m_date:
                continue
            meas_fields = [
                "waist_cm", "chest_cm", "left_arm_cm", "right_arm_cm",
                "left_thigh_cm", "right_thigh_cm", "hips_cm",
                "left_calf_cm", "right_calf_cm", "shoulders_cm", "neck_cm",
            ]
            defaults = {f: m.get(f) for f in meas_fields}
            defaults["notes"] = m.get("notes", "")
            _, created = MeasurementLog.objects.get_or_create(
                user=request.user, date=m_date,
                defaults=defaults,
            )
            if created:
                results["created"]["measurements"] += 1
            else:
                results["skipped"]["measurements"] += 1

        # 6. Workout Templates
        for tpl_data in data.get("workout_templates", []):
            tpl_name = tpl_data.get("name", "").strip()
            if not tpl_name:
                continue
            tpl, created = WorkoutTemplate.objects.get_or_create(
                user=request.user, name=tpl_name,
                defaults={
                    "description": tpl_data.get("description", ""),
                    "is_public": tpl_data.get("is_public", False),
                },
            )
            if created:
                for te_data in tpl_data.get("exercises", []):
                    ex_name = te_data.get("exercise_name", "").strip()
                    if not ex_name:
                        continue
                    exercise = Exercise.objects.filter(
                        user__in=[request.user, None], name=ex_name
                    ).first()
                    if exercise:
                        WorkoutTemplateExercise.objects.create(
                            template=tpl,
                            exercise=exercise,
                            order=te_data.get("order", 0),
                            target_sets=te_data.get("target_sets"),
                            target_reps_min=te_data.get("target_reps_min"),
                            target_reps_max=te_data.get("target_reps_max"),
                        )
                results["created"]["workout_templates"] += 1
            else:
                results["skipped"]["workout_templates"] += 1

        # 7. Workouts
        for w_data in data.get("workouts", []):
            w_date = w_data.get("date")
            if not w_date:
                continue
            tpl_name = w_data.get("template_name")
            tpl = None
            if tpl_name:
                tpl = WorkoutTemplate.objects.filter(user=request.user, name=tpl_name).first()
            lookup = {"user": request.user, "date": w_date}
            if tpl:
                lookup["template"] = tpl
            existing = Workout.objects.filter(**lookup).first()
            if existing:
                results["skipped"]["workouts"] += 1
                continue
            workout = Workout.objects.create(
                user=request.user,
                date=w_date,
                template=tpl,
                duration_minutes=w_data.get("duration_minutes"),
                notes=w_data.get("notes", ""),
            )
            for we_data in w_data.get("exercises", []):
                ex_name = we_data.get("exercise_name", "").strip()
                if not ex_name:
                    continue
                exercise = Exercise.objects.filter(
                    user__in=[request.user, None], name=ex_name
                ).first()
                if not exercise:
                    results["errors"].append(f"Workout {w_date}: exercise '{ex_name}' not found, skipping")
                    continue
                we = WorkoutExercise.objects.create(
                    workout=workout,
                    exercise=exercise,
                    order=we_data.get("order", 0),
                )
                for s_data in we_data.get("sets", []):
                    Set.objects.create(
                        workout_exercise=we,
                        set_number=s_data.get("set_number", 1),
                        reps=s_data.get("reps"),
                        weight_kg=s_data.get("weight_kg"),
                        is_warmup=s_data.get("is_warmup", False),
                    )
            results["created"]["workouts"] += 1

        # 8. Cardio Logs
        for c_data in data.get("cardio_logs", []):
            c_date = c_data.get("date")
            activity = c_data.get("activity", "").strip()
            if not c_date or not activity:
                continue
            _, created = CardioLog.objects.get_or_create(
                user=request.user, date=c_date, activity=activity,
                defaults={
                    "duration_minutes": c_data.get("duration_minutes", 0),
                    "distance_km": c_data.get("distance_km"),
                    "notes": c_data.get("notes", ""),
                },
            )
            if created:
                results["created"]["cardio_logs"] += 1
            else:
                results["skipped"]["cardio_logs"] += 1

        # 9. Body Fat Logs
        for b_data in data.get("body_fat_logs", []):
            b_date = b_data.get("date")
            if not b_date:
                continue
            _, created = BodyFatLog.objects.get_or_create(
                user=request.user, date=b_date,
                defaults={
                    "body_fat_pct": b_data.get("body_fat_pct", 0),
                    "method": b_data.get("method", "manual"),
                    "notes": b_data.get("notes", ""),
                },
            )
            if created:
                results["created"]["body_fat_logs"] += 1
            else:
                results["skipped"]["body_fat_logs"] += 1

        # 10. Photos
        for p_data in data.get("photos", []):
            p_date = p_data.get("date")
            body_part = p_data.get("body_part", "front")
            if not p_date:
                continue
            existing = ProgressPhoto.objects.filter(
                user=request.user, date=p_date, body_part=body_part
            ).first()
            if existing:
                results["skipped"]["photos"] += 1
                continue
            b64 = p_data.get("image_base64")
            if not b64:
                results["errors"].append(f"Photo {p_date} ({body_part}): no image data, skipping")
                continue
            try:
                raw = base64.b64decode(b64)
                filename = p_data.get("image_filename", f"photo_{p_date}_{body_part}.jpg")
                photo = ProgressPhoto(
                    user=request.user,
                    date=p_date,
                    body_part=body_part,
                    notes=p_data.get("notes", ""),
                )
                photo.image.save(filename, ContentFile(raw), save=True)
                results["created"]["photos"] += 1
            except Exception as e:
                results["errors"].append(f"Photo {p_date} ({body_part}): {e}")

        results["created"] = dict(results["created"])
        results["updated"] = dict(results["updated"])
        results["skipped"] = dict(results["skipped"])
        return render(request, "tracker/import_export.html", {
            "import_results": results,
        })

    messages.error(request, "Invalid request.")
    return redirect("tracker:import_export")
