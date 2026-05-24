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
```

## App Structure
- `accounts/` — Registration, login, profile (unit preferences)
- `tracker/` — Weight, measurements, exercises, workouts, sets
- `photos/` — Progress photos

## URLs
- `/` — Dashboard
- `/accounts/` — Auth
- `/admin/` — Django admin (staff only)
- `/weight/` — Weight logs
- `/measurements/` — Body measurements
- `/exercises/` — Exercise library
- `/templates/` — Workout templates
- `/workouts/` — Workout logging
- `/photos/` — Progress photos
- `/export/` — CSV export
