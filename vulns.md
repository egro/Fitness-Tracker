# Security Audit Report — Fitness Tracker

**Date:** 2026-05-30 (Updated)
**Scope:** Full Django application

---

## Status Key

| Icon | Meaning |
|------|---------|
| ✅ | Fixed |
| ❌ | Not fixed |
| ➖ | Skipped by request (TLS/SSL or email verification) |

---

## 🔴 HIGH Severity

### H1 — DEBUG mode defaults to `true`

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:11` |
| **Fix** | Default changed to `"false"`. Set `DJANGO_DEBUG=true` in `.env` for local dev. |

---

### H2 — Weak / predictable SECRET_KEY

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:10`, `.env` |
| **Fix** | `SECRET_KEY` is now required (no fallback). A random 50-char key is in `.env`. |

---

### H3 — ALLOWED_HOSTS wildcard

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:12`, `.env` |
| **Fix** | Defaults to empty list. Set to `localhost,127.0.0.1` in `.env` for dev. |

---

### H4 — Stored XSS via exercise name in inline JavaScript

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **Files** | `tracker/templates/tracker/exercise_list.html:31`, `muscle_list.html:27,52` |
| **Fix** | Added `|escapejs` filter to all `confirm()` dialogs using exercise names. |

---

### H5 — Container runs as root

| Field | Value |
|-------|-------|
| **Status** | ❌ **Not fixed** |
| **File** | `Dockerfile` |
| **Issue** | gunicorn runs as root. If compromised, attacker gains root inside container. |
| **Fix** | Add `RUN adduser --disabled-password --no-create-home appuser` then `USER appuser`. Ensure `/app/data` and `/app/media` are writable. |

---

## 🟡 MEDIUM Severity

### M1 — Insufficient password validation

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:66-70` |
| **Fix** | All four Django password validators are now active. |

---

### M2 — No session security hardening (non-SSL parts)

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:88-92` |
| **Fix** | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`, `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`, `CSRF_COOKIE_HTTPONLY=True`, `SECURE_REFERRER_POLICY="same-origin"`. |

---

### M3 — No HTTPS / SSL configuration

| Field | Value |
|-------|-------|
| **Status** | ➖ **Skipped** |
| **Note** | User handles SSL via reverse proxy. `manage.py check --deploy` shows 5 expected TLS warnings. |

---

### M4 — Raw POST handling with no validation

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `tracker/views.py` |
| **Fix** | Added `_safe_float()`, `_safe_int()`, `_safe_str()` helpers. Applied across all views that parse `request.POST` directly. `float()`/`int()` casts no longer raise `ValueError` on bad input; string fields are capped to `max_length`. |

---

### M5 — workout_exercise_add skips user ownership check

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `tracker/views.py:828` |
| **Fix** | Added `user__in=[request.user, None]` filter to exercise lookup. |

---

### M6 — Model `__str__` leaks personal health data

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **Files** | `tracker/models.py`, `photos/models.py` |
| **Fix** | Removed `user.username` from `__str__` on `WeightLog`, `MeasurementLog`, `Workout`, `CardioLog`, `ProgressPhoto`. |

---

### M7 — No rate limiting on login / register

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **Files** | `accounts/views.py:16,22`, `requirements.txt` |
| **Fix** | Added `django-ratelimit`. Login limited to 10/min per IP, register to 5/min per IP. |

---

### M8 — No email verification on registration

| Field | Value |
|-------|-------|
| **Status** | ➖ **Skipped** |

---

### M9 — Raw float() with no exception handling in measurement_add

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** (covered by M4) |

---

### M10 — No CSRF_TRUSTED_ORIGINS configured

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `config/settings.py:13`, `.env` |
| **Fix** | `CSRF_TRUSTED_ORIGINS` is configurable via `DJANGO_CSRF_TRUSTED_ORIGINS` env var. Defaults to empty list for local dev. |

---

## 🔵 LOW Severity

### L1 — Username in photo upload path

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `photos/models.py:6` |
| **Fix** | Changed from `user.username` to `user.pk`. |

---

### L2 — No server-side file validation on photo uploads

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `photos/views.py` |
| **Fix** | Added `FileExtensionValidator` (jpg, jpeg, png, gif, webp) and 10 MB size limit. |

---

### L3 — CSRF_COOKIE_SECURE not set

| Field | Value |
|-------|-------|
| **Status** | ➖ **Skipped** (TLS-related) |

---

### L4 — Media served via Django / no auth on media URLs

| Field | Value |
|-------|-------|
| **Status** | ➖ **Mitigated by H1** |
| **Note** | `static()` helper only activates when `DEBUG=True`. In production (`DEBUG=False`), media files must be served by the reverse proxy. |

---

### L5 — date_of_birth can be set in the future

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `accounts/forms.py:82` |
| **Fix** | Added `MaxValueValidator(date.today())` to date_of_birth field. |

---

### L6 — No input length limits on POST fields

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** (covered by M4) |
| **Note** | `_safe_str(val, max_len=N)` applied to all user-facing string fields. |

---

### L7 — Theme variable in inline JS without escapejs

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `templates/base.html:6` |
| **Fix** | Added `|escapejs` to `theme` and `nav_color_hex` in the inline `<script>` block. |

---

### L8 — SECURE_REFERRER_POLICY not set

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** (covered by M2) |

---

### L9 — Password help text leaks validator information

| Field | Value |
|-------|-------|
| **Status** | ✅ **Fixed** |
| **File** | `accounts/forms.py:25` |
| **Fix** | Replaced Django's default verbose help text with a concise custom message. |

---

## 🔴 Remaining HIGH Severity

| Item | Issue | 
|------|-------|
| **H5** | Container runs as root — requires Dockerfile change |

## 🟡 Remaining MEDIUM Severity

| Item | Issue |
|------|-------|
| — | None — all fixed or skipped |

## 🔵 Remaining LOW Severity

| Item | Issue |
|------|-------|
| — | None — all fixed or skipped |

## 📌 Additional finding during rescan

### N1 — Potential XSS in category_list.html

| Field | Value |
|-------|-------|
| **File** | `tracker/templates/tracker/category_list.html:28` |
| **Issue** | `onsubmit="return confirm('Delete category &#39;{{ cat.name }}&#39;?')"` — uses HTML entity `&#39;` to escape single quotes, but the HTML parser decodes it before JavaScript evaluates it. A category name with `'; alert(1); '` would still execute. |
| **Severity** | 🔴 HIGH (stored XSS, same class as H4) |
| **Fix** | Replace with `|escapejs` filter: `onsubmit="return confirm('Delete category {{ cat.name|escapejs }}?')"` |

---

## Django `check --deploy` Warnings (expected)

These are all TLS/SSL-related and intentionally skipped:

```
?: (security.W004) SECURE_HSTS_SECONDS not set.
?: (security.W008) SECURE_SSL_REDIRECT not set to True.
?: (security.W012) SESSION_COOKIE_SECURE not set to True.
?: (security.W016) CSRF_COOKIE_SECURE not set to True.
?: (security.W018) DEBUG set to True in development.
```

---

## Summary

| Severity | Total | Fixed | Skipped | Remaining |
|----------|-------|-------|---------|-----------|
| HIGH     | 5     | 3     | 0       | 2 (H5, N1) |
| MEDIUM   | 10    | 8     | 2       | 0         |
| LOW      | 9     | 7     | 2       | 0         |

**Remaining work:** Fix H5 (root container) and N1 (XSS in category_list.html).
