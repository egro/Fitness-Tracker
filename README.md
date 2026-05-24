# Fitness Tracker

Self-hosted fitness tracking app for you and a partner. Track weight, body measurements, exercises, workouts, sets, and progress photos — all with per-user accounts and metric/imperial support.

## Features

- **Multi-user** with data isolation (each user sees only their own data; admin sees all)
- **Per-user units** — metric (kg/cm) or imperial (lbs/in), toggled in settings
- **Dashboard** — latest weight, 180-day weight trend chart, 180-day measurements chart
- **Weight tracking** — log with auto-converting kg/lbs fields, history table, trend chart
- **Body measurements** — 11 measurement points (waist, chest, arms, thighs, calves, hips, shoulders, neck)
- **Exercise library** — organized by category, with inline category creation
- **Workout templates** — reusable routines you build and start from
- **Workout logging** — start from a template or blank, add exercises, log sets (reps/weight/RIR) with auto-converting kg/lbs inputs
- **Progress photos** — upload multiple at once, gallery view
- **CSV export** — download weight, measurements, or workout data
- **Django admin** — full admin panel for staff users at `/admin/`
- **Mobile-friendly** — responsive layout with Tailwind CSS

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python / Django 5+ |
| Frontend | Django templates + Tailwind CSS (CDN) |
| Dynamic UI | HTMX (CDN) |
| Charts | Chart.js (CDN) |
| Database | SQLite (file-based, zero config) |
| Static files | whitenoise |
| Container | Docker + gunicorn |

## Quick Start

### Local development

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate
venv/bin/python manage.py createsuperuser
venv/bin/python manage.py runserver 0.0.0.0:8000
```

### With Docker

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

The app runs at `http://localhost:8000`.

## Project Structure

```
fitness-tracker/
├── accounts/          # Registration, login, profile (unit prefs)
│   ├── models.py      # Profile model (extends User)
│   ├── views.py       # Register, login, profile views
│   └── templates/accounts/
├── tracker/           # Core tracking app
│   ├── models.py      # WeightLog, MeasurementLog, Exercise, Workout, Set, etc.
│   ├── views.py       # All CRUD views + export + chart data
│   ├── utils.py       # Unit conversion helpers
│   ├── templatetags/  # Custom template filters (convert_wt, convert_len, etc.)
│   └── templates/tracker/
├── photos/            # Progress photo uploads & gallery
│   ├── models.py      # ProgressPhoto model
│   └── templates/photos/
├── config/            # Django project settings
│   ├── settings.py
│   └── urls.py
├── templates/         # Shared templates
│   └── base.html
├── data/              # SQLite database (docker volume)
├── media/             # Uploaded photos (docker volume)
├── Dockerfile
└── docker-compose.yml
```

## URLs

| URL | Page |
|---|---|
| `/` | Dashboard (weight chart, measurements chart, recent workouts) |
| `/accounts/login/` | Login |
| `/accounts/register/` | Register |
| `/accounts/profile/` | Settings (unit preference) |
| `/weight/` | Weight history |
| `/weight/add/` | Log weight |
| `/measurements/` | Measurement history |
| `/measurements/add/` | Log measurements |
| `/exercises/` | Exercise library |
| `/exercises/add/` | Add exercise |
| `/templates/` | Workout templates |
| `/templates/add/` | Create template |
| `/workouts/` | Workout history |
| `/workouts/add/` | Start workout |
| `/photos/` | Photo gallery |
| `/photos/upload/` | Upload photos |
| `/export/` | CSV data export |
| `/admin/` | Django admin (staff only) |

## Data Models

- **Profile** — extends User with unit preference (metric/imperial) and date of birth
- **WeightLog** — date, weight in kg, notes (one entry per user per date)
- **MeasurementLog** — date, 11 body part measurements in cm, notes
- **ExerciseCategory** — user or global, groups exercises
- **Exercise** — name, category, user or global
- **WorkoutTemplate** — reusable routine with ordered exercises
- **WorkoutTemplateExercise** — exercise + order + optional targets (sets, reps, weight)
- **Workout** — date, optional template reference, duration, notes
- **WorkoutExercise** — exercise logged in a specific workout
- **Set** — reps, weight in kg, RIR (reps in reserve), warmup flag
- **ProgressPhoto** — image file, date, body part label, notes

## Configuration

Environment variables (for production Docker deployment):

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `dev-secret-key...` | Django secret key |
| `DJANGO_DEBUG` | `true` | Debug mode (`true`/`false`) |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated hosts |

## Data Ownership

- All data is stored locally in `data/db.sqlite3` (SQLite)
- Photos are stored in `media/` on the filesystem
- Export any dataset as CSV from `/export/`
