# Fitness Tracker

Self-hosted fitness tracking app for you and a partner. Track weight, body measurements, exercises, workouts, sets, and progress photos — all with per-user accounts and metric/imperial support.

## Features

- **Multi-user** with data isolation (each user sees only their own data; admin sees all)
- **Per-user units** — metric (kg/cm) or imperial (lbs/in), toggled in settings
- **Dashboard** — latest weight, 180-day weight trend chart, 180-day measurements chart, per-exercise weight progression chart
- **Weight tracking** — log with auto-converting kg/lbs fields, history table, trend chart
- **Body measurements** — 11 measurement points (waist, chest, arms, thighs, calves, hips, shoulders, neck)
- **Exercise library** — flat list sorted by name, shows muscle group tags; separate **Muscle Library** grouped by muscle group
- **Categories** — add, rename, and delete muscle groups/categories
- **Workout templates** — reusable routines with target sets, min/max reps, and target weight per exercise; create, view, edit, and delete
- **Workout logging** — start from a template or blank, add exercises, log sets (reps/weight) with auto-converting kg/lbs inputs and auto-suggested weight based on progressive overload
- **Progressive overload** — tracks whether all sets hit max reps; auto-suggests next weight (+5 lbs if goal met, same weight if not) pre-filled into the Add Set form
- **Customizable navigation** — reorder and toggle which items appear as header quick links; full item list always available in hamburger menu
- **Progress photos** — upload multiple at once, gallery view
- **CSV export** — download weight, measurements, or workout data
- **Django admin** — full admin panel for staff users at `/admin/`
- **Mobile-friendly** — responsive layout with Tailwind CSS

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python / Django 6 |
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
├── accounts/          # Registration, login, profile, nav customization
│   ├── models.py      # Profile model, NavItem model, default nav seeding
│   ├── views.py       # Register, login, profile, nav_items views
│   └── templates/accounts/
├── tracker/           # Core tracking app
│   ├── models.py      # Exercise, WorkoutTemplate, Workout, Set, etc.
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
├── templates/         # Shared templates (base.html with nav)
├── data/              # SQLite database (docker volume)
├── media/             # Uploaded photos (docker volume)
├── Dockerfile
└── docker-compose.yml
```

## URLs

| URL | Page |
|---|---|
| `/` | Dashboard (weight chart, measurements chart, exercise progression) |
| `/accounts/login/` | Login |
| `/accounts/register/` | Register |
| `/accounts/profile/` | Settings (unit preference, date of birth) |
| `/accounts/nav-items/` | Customize navigation (reorder, toggle header visibility) |
| `/weight/` | Weight history |
| `/weight/add/` | Log weight |
| `/measurements/` | Measurement history |
| `/measurements/add/` | Log measurements |
| `/categories/` | Manage muscle groups/categories |
| `/exercises/` | Exercise library (flat, sorted by name with muscle tags) |
| `/exercises/add/` | Add exercise |
| `/exercises/<pk>/edit/` | Edit exercise |
| `/muscles/` | Muscle library (grouped by muscle group) |
| `/templates/` | Workout templates |
| `/templates/add/` | Create template (with target sets, reps, weight) |
| `/templates/<pk>/edit/` | Edit template |
| `/workouts/` | Workout history |
| `/workouts/add/` | Start workout |
| `/photos/` | Photo gallery |
| `/photos/upload/` | Upload photos |
| `/export/` | CSV data export |
| `/admin/` | Django admin (staff only) |

## Data Models

- **Profile** — extends User with unit preference (metric/imperial) and date of birth
- **NavItem** — per-user navigation items with label, URL, order, visibility, and system flag
- **WeightLog** — date, weight in kg, notes (one entry per user per date)
- **MeasurementLog** — date, 11 body part measurements in cm, notes
- **ExerciseCategory** — user or global, groups exercises (muscle groups)
- **Exercise** — name, categories (M2M — multiple muscle groups), user or global
- **WorkoutTemplate** — reusable routine with ordered exercises
- **WorkoutTemplateExercise** — exercise + order + targets (sets, min/max reps, weight)
- **Workout** — date, optional template reference, duration, notes
- **WorkoutExercise** — exercise logged in a specific workout, with copied target fields
- **Set** — reps, weight in kg, warmup flag
- **ProgressPhoto** — image file, date, body part label, notes

## Progressive Overload

When logging a workout from a template:
1. Each exercise shows its target (e.g., `3 sets x 8-12 reps`)
2. The **Add Set** form is pre-filled with the suggested weight based on your last workout for that exercise
3. If all working sets hit the max rep target last time, the suggestion increases by 5 lbs
4. If not all sets hit max reps, the same weight is suggested
5. A label explains whether the weight went up or stayed the same

## Customizable Navigation

The hamburger menu always shows every available page. The header bar shows only the items you mark as visible. To customize:

1. Go to **Settings** → **Customize Navigation Menu**
2. Use ▲/▼ to reorder items
3. Click the dot to toggle header visibility
4. System items (Settings, Logout) are locked and always appear at the bottom of the menu

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
