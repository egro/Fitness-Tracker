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
- `accounts/` — Registration, login, profile (theme, height, goal weight, DOB)
- `tracker/` — Weight, measurements, exercises, workouts, sets, cardio
- `photos/` — Progress photos

## Profile Model (`accounts/models.py`)
- `date_of_birth` — DateField (optional)
- `height_cm` — FloatField for BMI calculation (optional)
- `goal_weight_kg` — FloatField for goal tracking on dashboard (optional)
- `sex` — CharField: "male" or "female"; used for US Navy body fat formula
- `theme` — CharField: "light", "dark", or "auto"; controls dark mode via `.dark` class on `<html>`; "auto" follows OS `prefers-color-scheme` and switches live via `matchMedia` listener
- `nav_color` — CharField: 8 preset colors (blue, slate, emerald, violet, amber, rose, cyan, stone); sets nav bar `background-color`
- `nav_color_hex` — `@property` that maps `nav_color` to its hex value using `NAV_COLOR_PRESETS`

## Settings Page (`/accounts/profile/`)
- Form fields: Date of Birth, Height, Goal Weight, Sex, Theme, Nav Bar Color
- Sex (Male/Female) required for US Navy body fat formula on the dashboard
- Height is used with latest weight to calculate BMI on the dashboard
- Goal Weight shows remaining lbs to gain/lose on the dashboard; weight change color flips based on goal direction (green when moving toward target, red when moving away)
- Theme toggles dark mode (CSS overrides in `base.html` for common Tailwind classes)
- Nav Bar Color shown as color swatch radio buttons; applies inline `style="background-color: ..."` on `<nav>`
- Nav hover/active states use `hover:bg-white/20` and `bg-black/20` for dynamic color compatibility

## Layout (`templates/base.html`)
- Page background includes a subtle repeating SVG dot pattern (dark dots in light mode, light dots in dark mode)
- Nav bar uses inline `style` with `user.profile.nav_color_hex` instead of a hardcoded Tailwind class
- Dark mode CSS overrides cover common Tailwind utilities (bg, text, border, input, alert colors)

## Dashboard Charts

All charts use Chart.js 4.4+ and render as line graphs.

### Weight Trend (180 days)
- Single blue line (`#2563eb`) with filled area
- Source: `WeightLog` entries

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
- `/cardio/` — Cardio activity log
- `/exercises/` — Exercise library
- `/templates/` — Workout templates
- `/workouts/` — Workout logging
- `/photos/` — Progress photos
- `/export/` — CSV export

## Cardio Log Model (`tracker/models.py`)
- `activity` — CharField for activity name (e.g. Swimming, Treadmill, Biking)
- `duration_minutes` — PositiveIntegerField for workout duration
- `distance_km` — DecimalField (optional) for distance in km; displayed as miles in templates
- `notes` — TextField for optional notes
- `CardioLog.objects.filter(user=request.user).order_by("-date")` for listing
