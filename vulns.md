# Security Audit Findings

## Fixed

### [HIGH] Stored XSS in category_list.html
- **File**: `tracker/templates/tracker/category_list.html:28`
- **Issue**: `cat.name` rendered inside `onsubmit` JS string without `|escapejs` filter. A user could name a category `'); alert('xss');//` and trigger JS execution.
- **Fix**: Applied `|escapejs` filter to `{{ cat.name }}` in the onsubmit handler.
- **Status**: Fixed

## Open

### [LOW] django-ratelimit installed but unused
- `django-ratelimit` is in `requirements.txt` and enabled in settings (`RATELIMIT_ENABLE`), but no views use `@ratelimit` decorator. This has no security impact but is dead config.

### [LOW] Secret key in `.env`
- `DJANGO_SECRET_KEY` is stored in plaintext in `.env`. This is standard practice, but ensure `.env` is not committed to version control and has restrictive file permissions (`chmod 600`).

## Dependency Versions (for reference)

| Package | Version | Notes |
|---|---|---|
| Django | 6.0.5 | Latest in 6.0.x; check for new point releases |
| djangorestframework | 3.17.1 | CVE-2024-21520 (XSS via `break_long_headers`) patched since 3.15.2 |
| Pillow | 12.2.0 | Latest; regularly update |
| djangorestframework-simplejwt | 5.5.0 | Regularly update |
| django-cors-headers | 4.7.0 | Regularly update |
