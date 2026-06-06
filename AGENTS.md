# Fitness Tracker - Dev Reference

## Commands

```bash
# Setup (first time)
python3 -m venv venv && venv/bin/pip install -r requirements.txt

# Run migrations
venv/bin/python manage.py migrate

# Create superuser
venv/bin/python manage.py createsuperuser

# Run dev server
venv/bin/python manage.py runserver 0.0.0.0:8000

# Run checks
venv/bin/python manage.py check

# Make migrations after model changes
venv/bin/python manage.py makemigrations

# Docker
docker compose up -d --build

# First run in Docker (create superuser):
docker compose exec web python manage.py createsuperuser

# Rebuild after any code changes (Python, HTML, CSS, JS):
docker compose up -d --build
```

## App Structure
- `accounts/` — Registration, login, profile (theme, height, goal weight, DOB, units, goal body fat)
- `tracker/` — Weight, measurements, body fat, exercises, workouts, sets, cardio
- `photos/` — Progress photos

## Profile Model (`accounts/models.py`)
- `date_of_birth` — DateField (optional)
- `height_cm` — FloatField for BMI calculation (optional)
- `goal_weight_kg` — FloatField for goal tracking on dashboard (optional)
- `goal_body_fat_pct` — FloatField for body fat goal on dashboard (optional)
- `sex` — CharField: "male" or "female"; used for US Navy body fat formula
- `units` — CharField: "metric" or "imperial"; controls unit display throughout the app
- `theme` — CharField: "light", "dark", or "auto"; controls dark mode via `.dark` class on `<html>`; "auto" follows OS `prefers-color-scheme` and switches live via `matchMedia` listener
- `nav_color` — CharField: 8 preset colors (blue, slate, emerald, violet, amber, rose, cyan, stone); sets nav bar `background-color`
- `nav_color_hex` — `@property` that maps `nav_color` to its hex value using `NAV_COLOR_PRESETS`

## Settings Page (`/accounts/profile/`)
- Form fields: Date of Birth, Height, Goal Weight, Goal Body Fat %, Sex, Units (Metric/Imperial), Theme, Nav Bar Color
- Sex (Male/Female) required for US Navy body fat formula on the dashboard
- Height is used with latest weight to calculate BMI on the dashboard
- Goal Weight shows remaining lbs/kg to gain/lose on the dashboard; weight change color flips based on goal direction (green when moving toward target, red when moving away)
- Goal Body Fat % shows remaining percentage to gain/lose on the dashboard
- Units affects all display: imperial shows lbs/in/mi, metric shows kg/cm/km; form fields convert on save
- Theme toggles dark mode (CSS overrides in `base.html` for common Tailwind classes)
- Nav Bar Color shown as color swatch radio buttons; applies inline `style="background-color: ..."` on `<nav>`
- Nav hover/active states use `hover:bg-white/20` and `bg-black/20` for dynamic color compatibility

## Layout (`templates/base.html`)
- Page background: interactive particle network (dots connected by lines, repels from mouse)
- Nav bar uses inline `style` with `user.profile.nav_color_hex` instead of a hardcoded Tailwind class
- Dark mode CSS overrides cover common Tailwind utilities (bg, text, border, input, alert colors)
- Chart expand: charts are clickable, expand to centered overlay with backdrop; CSS class `.chart-card.expanded` toggles fixed positioning; `Esc` or backdrop click closes; `toggleChart()` JS function handles class toggling and `ch.resize()`

## Dashboard Charts

All charts use Chart.js 4.4+ and render as line graphs. Charts are in a 2-column grid (`md:grid-cols-2`) on desktop, single-column on mobile. All charts have `maintainAspectRatio: false` so they fill their container. Chart cards have `height: 300px` (280px on mobile). Click any chart to expand it to a centered overlay at 65vh tall.

### Combined Weight & Body Fat (180 days)
- Weight: blue line (`#2563eb`) with filled area, left y-axis (`spanGaps: true`)
- Body Fat: red line (`#ef4444`), right y-axis (`spanGaps: false`)
- Direct `BodyFatLog` entries appear as triangles with larger radius; Navy-calculated points are small circles
- Tooltip shows method name for direct entries or "Navy calc" for calculated
- Date axis merges weight log dates, measurement dates, and BodyFatLog dates
- Source: `WeightLog` entries + Navy formula from `MeasurementLog` + `BodyFatLog` entries

### Body Measurements (180 days)
- All body parts on one chart, each with a distinct color
- Click a legend item to toggle that measurement on/off
- Gaps shown for missing measurement days (`spanGaps: false`)
- Source: `MeasurementLog` fields (waist, chest, arms, thighs, etc.)

### Exercise Progression
- All exercises on one chart, each with a distinct color
- Click a legend item to toggle that exercise on/off
- Gaps shown for dates with no data (`spanGaps: false`)
- Tooltip shows rep count for each data point
- Source: `WorkoutExercise` → heaviest working `Set` per exercise per date (kg converted to lbs)
- View: `tracker/views.py` `dashboard()` builds datasets aligned to shared date axis
- Colors auto-assigned from a 15-color palette, cycled if more exercises exist

### Cardio Activity (180 days)
- All activities on one chart, each with a distinct color
- Click a legend item to toggle that activity on/off
- Gaps shown for dates with no data (`spanGaps: false`)
- Tooltip shows duration in minutes
- Source: `CardioLog` entries grouped by activity name
- Colors auto-assigned from the same 15-color palette

## URLs
- `/` — Dashboard
- `/accounts/` — Auth
- `/admin/` — Django admin (staff only)
- `/weight/` — Weight logs
- `/measurements/` — Body measurements
- `/bodyfat/` — Body fat log
- `/cardio/` — Cardio activity log
- `/exercises/` — Exercise library
- `/templates/` — Workout templates
- `/workouts/` — Workout logging
- `/photos/` — Progress photos
- `/export/` — CSV export & import

## BodyFatLog Model (`tracker/models.py`)
- `date` — DateField
- `body_fat_percentage` — FloatField (the logged %)
- `method` — CharField with choices: dexa, caliper, bodpod, scale_bia, photo_3d, manual
- `notes` — TextField (optional)
- `Meta.ordering = ["-date", "-created_at"]` — duplicate dates resolved by most recently created
- `BodyFatLog.objects.filter(user=request.user)` for queries

## Cardio Log Model (`tracker/models.py`)
- `activity` — CharField for activity name (e.g. Swimming, Treadmill, Biking)
- `duration_minutes` — PositiveIntegerField for workout duration
- `distance_km` — DecimalField (optional) for distance in km; displayed as miles in templates
- `notes` — TextField for optional notes
- `CardioLog.objects.filter(user=request.user).order_by("-date")` for listing

## Workout Detail / Weight Suggestions (`tracker/views.py` `workout_detail()`)
- When a `WorkoutExercise` already has sets, suggestion = weight of the last non-warmup set ("from last set")
- When no sets yet, looks up the most recent historical `WorkoutExercise` for the same exercise that **has actual sets** (skips entries where the exercise was skipped)
- Uses the first non-warmup set from that historical workout as baseline
- If all target sets hit `target_reps_max`, suggests +5 lbs; otherwise suggests "same" weight

## API (`api/`)

Django REST Framework API with JWT authentication. All data in metric (kg/cm/km). All endpoints require `Authorization: Bearer <token>` except register/login.

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Create account (username, email, password) |
| POST | `/api/auth/login/` | No | Get JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | No | Refresh expired access token |
| GET | `/api/auth/me/` | Yes | Current user + profile |
| GET/PATCH | `/api/profile/` | Yes | Get/update profile settings |

### CRUD Endpoints (standard list/create/retrieve/update/destroy)

All paginated at 50 per page, throttled at 1000 req/hr per user.

| Endpoint | Model |
|---|---|
| `/api/weight/` | WeightLog |
| `/api/measurements/` | MeasurementLog |
| `/api/bodyfat/` | BodyFatLog |
| `/api/cardio/` | CardioLog |
| `/api/exercises/` | Exercise |
| `/api/categories/` | ExerciseCategory |
| `/api/templates/` | WorkoutTemplate (nested exercises) |
| `/api/template-exercises/` | WorkoutTemplateExercise |
| `/api/workouts/` | Workout (nested exercises + sets) |
| `/api/workout-exercises/` | WorkoutExercise |
| `/api/sets/` | Set |
| `/api/photos/` | ProgressPhoto (multipart image upload) |

### Dashboard Endpoints (read-only)

| Endpoint | Description |
|---|---|
| `/api/dashboard/summary/` | Latest weight, BMI, body fat, lean/fat mass, goal progress |
| `/api/dashboard/charts/weight/` | Combined weight + body fat chart data (query: `?days=180`) |
| `/api/dashboard/charts/measurements/` | All 11 measurement points (query: `?days=180`) |
| `/api/dashboard/charts/exercises/` | Exercise weight progression (query: `?days=365`) |
| `/api/dashboard/charts/cardio/` | Cardio activity chart data (query: `?days=180`) |

### Dashboard Summary Card
- Shows latest body fat % with method badge (colored pill: DEXA purple, caliper yellow, BOD POD blue, scale/BIA green, 3D photo indigo, manual gray)
- Info tooltip (ℹ️) displays US Navy formula for both sexes
- If Navy calc differs from latest entry, shows "Navy calc: X%" in lighter text below
- Shows lean mass and fat mass in current weight unit when both weight and BF are available
