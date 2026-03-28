# Placement Portal Application (PPA) - V2 (Scaffold)

This folder contains a scaffold for a Flask (API) + Vue (CDN entry UI) + SQLite + Redis + Celery project.

## Backend (Flask + SQLite)
1. Open PowerShell in `backend/`
2. Install dependencies:
   - `python -m pip install -r requirements.txt`
3. Ensure Redis is running locally (defaults below):
   - `REDIS_URL=redis://localhost:6379/0`
   - `CELERY_BROKER_URL=redis://localhost:6379/1`
   - `CELERY_RESULT_BACKEND=redis://localhost:6379/2`
4. Start the API/UI:
   - `python run.py`

### Default Admin Credentials (created programmatically)
- Email: `admin@ppa.local`
- Password: `admin123`

## Celery
Run a worker (from `backend/`):
- `python -m celery -A app.tasks.celery_app.celery_app worker --loglevel=info`

Run beat scheduler (from `backend/`):
- `python -m celery -A app.tasks.celery_app.celery_app beat --loglevel=info`

## Email Notifications
Background jobs are safe by default: if `EMAIL_USER`/`EMAIL_PASSWORD` are not set, emails will be skipped.

## UI
Open:
- `http://localhost:5000/`

## API (quick pointers)
- Auth: `/api/auth/*`
- Admin: `/api/admin/*`
- Company: `/api/company/*`
- Student: `/api/student/*`

