from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r"weight", views.WeightLogViewSet, basename="weight")
router.register(r"measurements", views.MeasurementLogViewSet, basename="measurements")
router.register(r"bodyfat", views.BodyFatLogViewSet, basename="bodyfat")
router.register(r"cardio", views.CardioLogViewSet, basename="cardio")
router.register(r"exercises", views.ExerciseViewSet, basename="exercises")
router.register(r"categories", views.ExerciseCategoryViewSet, basename="categories")
router.register(r"templates", views.WorkoutTemplateViewSet, basename="templates")
router.register(r"template-exercises", views.WorkoutTemplateExerciseViewSet, basename="template-exercises")
router.register(r"workouts", views.WorkoutViewSet, basename="workouts")
router.register(r"workout-exercises", views.WorkoutExerciseViewSet, basename="workout-exercises")
router.register(r"sets", views.SetViewSet, basename="sets")
router.register(r"photos", views.ProgressPhotoViewSet, basename="photos")

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("dashboard/summary/", views.DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/charts/weight/", views.DashboardChartWeightView.as_view(), name="dashboard-chart-weight"),
    path("dashboard/charts/measurements/", views.DashboardChartMeasurementsView.as_view(), name="dashboard-chart-measurements"),
    path("dashboard/charts/exercises/", views.DashboardChartExercisesView.as_view(), name="dashboard-chart-exercises"),
    path("dashboard/charts/cardio/", views.DashboardChartCardioView.as_view(), name="dashboard-chart-cardio"),
]

urlpatterns += router.urls
