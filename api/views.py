import math
from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.models import User
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.models import Profile
from tracker.models import (
    ExerciseCategory, Exercise, WeightLog, MeasurementLog, BodyFatLog,
    WorkoutTemplate, WorkoutTemplateExercise, Workout, WorkoutExercise, Set,
    CardioLog,
)
from photos.models import ProgressPhoto
from .serializers import (
    UserSerializer, RegisterSerializer, UserDetailSerializer, ProfileSerializer,
    WeightLogSerializer, MeasurementLogSerializer, BodyFatLogSerializer,
    CardioLogSerializer, ExerciseCategorySerializer, ExerciseSerializer,
    WorkoutTemplateSerializer, WorkoutTemplateExerciseSerializer,
    WorkoutSerializer, WorkoutListSerializer, WorkoutExerciseSerializer,
    SetSerializer, ProgressPhotoSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserDetailSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class WeightLogViewSet(viewsets.ModelViewSet):
    serializer_class = WeightLogSerializer

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MeasurementLogViewSet(viewsets.ModelViewSet):
    serializer_class = MeasurementLogSerializer

    def get_queryset(self):
        return MeasurementLog.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BodyFatLogViewSet(viewsets.ModelViewSet):
    serializer_class = BodyFatLogSerializer

    def get_queryset(self):
        return BodyFatLog.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CardioLogViewSet(viewsets.ModelViewSet):
    serializer_class = CardioLogSerializer

    def get_queryset(self):
        return CardioLog.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseCategorySerializer

    def get_queryset(self):
        return ExerciseCategory.objects.filter(
            user=self.request.user
        ).order_by("name") | ExerciseCategory.objects.filter(
            user__isnull=True
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer

    def get_queryset(self):
        return Exercise.objects.filter(
            user=self.request.user
        ).order_by("name") | Exercise.objects.filter(
            user__isnull=True
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutTemplateSerializer

    def get_queryset(self):
        return WorkoutTemplate.objects.filter(user=self.request.user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutTemplateExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutTemplateExerciseSerializer

    def get_queryset(self):
        return WorkoutTemplateExercise.objects.filter(
            template__user=self.request.user
        ).order_by("order")

    def perform_create(self, serializer):
        template = serializer.validated_data["template"]
        if template.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()


class WorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user).order_by("-date")

    def get_serializer_class(self):
        if self.action == "list":
            return WorkoutListSerializer
        return WorkoutSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutExerciseSerializer

    def get_queryset(self):
        return WorkoutExercise.objects.filter(
            workout__user=self.request.user
        ).order_by("order")

    def perform_create(self, serializer):
        workout = serializer.validated_data["workout"]
        if workout.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.workout.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()


class SetViewSet(viewsets.ModelViewSet):
    serializer_class = SetSerializer

    def get_queryset(self):
        return Set.objects.filter(
            workout_exercise__workout__user=self.request.user
        ).order_by("set_number")

    def perform_create(self, serializer):
        we = serializer.validated_data["workout_exercise"]
        if we.workout.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_update(self, serializer):
        we = serializer.instance.workout_exercise
        if we.workout.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.workout_exercise.workout.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()


class ProgressPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressPhotoSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return ProgressPhoto.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            self.permission_denied(self.request)
        instance.image.delete(save=False)
        instance.delete()


# ── Dashboard / Summary / Chart endpoints ────────────────────────


def _navy_body_fat(profile, measurement):
    if not (profile.height_cm and measurement.waist_cm and measurement.neck_cm):
        return None
    waist = float(measurement.waist_cm)
    neck = float(measurement.neck_cm)
    height_cm = float(profile.height_cm)
    if waist <= neck:
        return None
    if profile.sex == "female":
        hips = float(measurement.hips_cm) if measurement.hips_cm else None
        if not hips:
            return None
        bf = 163.205 * math.log10(waist + hips - neck) - 97.684 * math.log10(height_cm) - 78.387
    else:
        bf = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height_cm) + 36.76
    if bf is not None and 3 < bf < 70:
        return round(bf, 1)
    return None


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)

        last_weight = WeightLog.objects.filter(user=user).order_by("-date").first()

        result = {
            "last_weight_kg": float(last_weight.weight_kg) if last_weight else None,
            "last_weight_date": str(last_weight.date) if last_weight else None,
            "bmi": None,
            "bmi_category": None,
            "body_fat_pct": None,
            "body_fat_method": None,
            "body_fat_navy_pct": None,
            "fat_mass_kg": None,
            "lean_mass_kg": None,
            "goal_weight_remaining_kg": None,
            "goal_weight_direction": None,
            "goal_weight_reached": False,
            "goal_body_fat_remaining_pct": None,
            "goal_body_fat_direction": None,
            "goal_body_fat_reached": False,
        }

        if not profile or not last_weight:
            return Response(result)

        if profile.height_cm:
            height_m = float(profile.height_cm) / 100.0
            bmi_val = float(last_weight.weight_kg) / (height_m ** 2)
            result["bmi"] = round(bmi_val, 1)
            if bmi_val < 18.5:
                result["bmi_category"] = "underweight"
            elif bmi_val < 25:
                result["bmi_category"] = "normal"
            elif bmi_val < 30:
                result["bmi_category"] = "overweight"
            else:
                result["bmi_category"] = "obese"

        if profile.goal_weight_kg:
            remaining = float(profile.goal_weight_kg) - float(last_weight.weight_kg)
            result["goal_weight_remaining_kg"] = round(abs(remaining), 2)
            result["goal_weight_direction"] = "gain" if remaining > 0 else "lose"
            result["goal_weight_reached"] = abs(remaining) < 0.1

        latest_meas = MeasurementLog.objects.filter(
            user=user, waist_cm__isnull=False, neck_cm__isnull=False
        ).order_by("-date").first()
        navy_pct = _navy_body_fat(profile, latest_meas) if latest_meas else None

        latest_direct = BodyFatLog.objects.filter(user=user).order_by("-date").first()

        if latest_direct:
            result["body_fat_pct"] = latest_direct.body_fat_pct
            result["body_fat_method"] = latest_direct.method
        elif navy_pct:
            result["body_fat_pct"] = navy_pct
            result["body_fat_method"] = "navy"

        result["body_fat_navy_pct"] = navy_pct

        if result["body_fat_pct"]:
            weight_kg = float(last_weight.weight_kg)
            fat_kg = weight_kg * result["body_fat_pct"] / 100.0
            result["fat_mass_kg"] = round(fat_kg, 2)
            result["lean_mass_kg"] = round(weight_kg - fat_kg, 2)

        if profile.goal_body_fat_pct and result["body_fat_pct"]:
            remaining = float(profile.goal_body_fat_pct) - result["body_fat_pct"]
            result["goal_body_fat_remaining_pct"] = round(abs(remaining), 1)
            result["goal_body_fat_direction"] = "gain" if remaining > 0 else "lose"
            result["goal_body_fat_reached"] = abs(remaining) < 0.1

        return Response(result)


class DashboardChartWeightView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)
        days = int(request.query_params.get("days", 180))
        cutoff = date.today() - timedelta(days=days)

        weight_logs = WeightLog.objects.filter(user=user, date__gte=cutoff).order_by("date")
        weight_labels = [str(l.date) for l in weight_logs]
        weight_values = [round(float(l.weight_kg), 2) for l in weight_logs]

        if not profile or not profile.height_cm or not weight_labels:
            return Response({
                "labels": weight_labels,
                "weight": weight_values,
                "body_fat": [],
                "body_fat_styles": [],
                "body_fat_methods": [],
            })

        meas_logs = list(MeasurementLog.objects.filter(
            user=user, date__gte=cutoff, waist_cm__isnull=False, neck_cm__isnull=False
        ).order_by("date"))

        bf_map = {}
        for m in meas_logs:
            bf = _navy_body_fat(profile, m)
            if bf:
                bf_map[str(m.date)] = bf

        direct_logs = BodyFatLog.objects.filter(user=user, date__gte=cutoff).order_by("date", "-created_at")
        direct_bf = {}
        for l in direct_logs:
            direct_bf[str(l.date)] = {"value": l.body_fat_pct, "method": l.method}

        if not bf_map and not direct_bf:
            return Response({
                "labels": weight_labels,
                "weight": weight_values,
                "body_fat": [],
                "body_fat_styles": [],
                "body_fat_methods": [],
            })

        all_sources = list(bf_map.keys()) + list(direct_bf.keys())
        all_dates = sorted(set(weight_labels + all_sources))

        weight_by_date = dict(zip(weight_labels, weight_values))
        merged_weight = [weight_by_date.get(d) for d in all_dates]

        sorted_navy_dates = sorted(bf_map.keys())
        merged_bf = []
        merged_styles = []
        merged_methods = []
        for d in all_dates:
            if d in direct_bf:
                merged_bf.append(direct_bf[d]["value"])
                merged_styles.append("direct")
                merged_methods.append(direct_bf[d]["method"])
            else:
                closest = None
                for nd in sorted_navy_dates:
                    if nd <= d:
                        closest = nd
                if closest:
                    merged_bf.append(bf_map[closest])
                    merged_styles.append("navy")
                    merged_methods.append("navy")
                else:
                    merged_bf.append(None)
                    merged_styles.append("navy")
                    merged_methods.append("navy")

        return Response({
            "labels": all_dates,
            "weight": merged_weight,
            "body_fat": merged_bf,
            "body_fat_styles": merged_styles,
            "body_fat_methods": merged_methods,
        })


class DashboardChartMeasurementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = int(request.query_params.get("days", 180))
        cutoff = date.today() - timedelta(days=days)
        logs = MeasurementLog.objects.filter(user=user, date__gte=cutoff).order_by("date")

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
            "waist_cm": "#3b82f6", "chest_cm": "#ef4444", "left_arm_cm": "#16a34a",
            "right_arm_cm": "#86efac", "left_thigh_cm": "#9333ea", "right_thigh_cm": "#c084fc",
            "hips_cm": "#f97316", "left_calf_cm": "#db2777", "right_calf_cm": "#f472b6",
            "shoulders_cm": "#14b8a6", "neck_cm": "#f59e0b",
        }

        labels = [str(l.date) for l in logs]
        datasets = []
        for field, label in fields:
            values = []
            for log in logs:
                val = getattr(log, field)
                values.append(round(float(val), 1) if val is not None else None)
            datasets.append({
                "label": label,
                "data": values,
                "borderColor": color_map[field],
                "spanGaps": False,
            })

        return Response({"labels": labels, "datasets": datasets})


class DashboardChartExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = int(request.query_params.get("days", 365))
        cutoff = date.today() - timedelta(days=days)

        wes = WorkoutExercise.objects.filter(
            workout__user=user, workout__date__gte=cutoff,
        ).select_related("exercise", "workout").prefetch_related("sets").order_by("workout__date")

        exercise_progress = defaultdict(list)
        for we in wes:
            working = [s for s in we.sets.all() if not s.is_warmup and s.weight_kg and float(s.weight_kg) > 0]
            if not working:
                continue
            heaviest = max(working, key=lambda s: float(s.weight_kg))
            exercise_progress[we.exercise.name].append({
                "date": str(we.workout.date),
                "weight_kg": round(float(heaviest.weight_kg), 2),
                "reps": heaviest.reps,
            })

        if not exercise_progress:
            return Response({"labels": [], "datasets": []})

        all_dates = sorted(set(
            d["date"] for points in exercise_progress.values() for d in points
        ))
        colors = [
            "#3b82f6", "#ef4444", "#16a34a", "#9333ea", "#f97316",
            "#14b8a6", "#db2777", "#f59e0b", "#06b6d4", "#84cc16",
            "#8b5cf6", "#ec4899", "#0ea5e9", "#a855f7", "#e11d48",
        ]
        datasets = []
        for i, (name, points) in enumerate(exercise_progress.items()):
            pt_map = {p["date"]: p for p in points}
            data = []
            reps = []
            for d in all_dates:
                if d in pt_map:
                    data.append(pt_map[d]["weight_kg"])
                    reps.append(pt_map[d]["reps"])
                else:
                    data.append(None)
                    reps.append(None)
            c = colors[i % len(colors)]
            datasets.append({
                "label": name,
                "data": data,
                "reps": reps,
                "borderColor": c,
                "spanGaps": True,
            })

        return Response({"labels": all_dates, "datasets": datasets})


class DashboardChartCardioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        days = int(request.query_params.get("days", 180))
        cutoff = date.today() - timedelta(days=days)
        logs = CardioLog.objects.filter(user=user, date__gte=cutoff).order_by("date")

        if not logs.exists():
            return Response({"labels": [], "datasets": []})

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
                data.append(pt_map[d]["duration"] if d in pt_map else None)
            c = colors[i % len(colors)]
            datasets.append({
                "label": activity,
                "data": data,
                "borderColor": c,
                "spanGaps": False,
            })

        return Response({"labels": all_dates, "datasets": datasets})
