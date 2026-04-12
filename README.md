# Placement Portal Application (PPA)

This is a Modern Application Development - II (MAD-2) project. It is a multi-role web-based application (Admin, Company, Student) built with a Flask Backend API and Vue.js Frontend.

## Prerequisites
- Python 3
- Redis (Required for Celery background tasks)

## How to Run the App

You will need to open **two separate terminal windows** to run this project properly (one for the main web server, and one for the background asynchronous tasks).

### Terminal 1: Run the Main Web Server
1. Navigate into the project folder.
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Run the Flask application:
   ```bash
   python backend/app.py
   ```
4. Open your browser and go to: **http://127.0.0.1:3000**

---

### Terminal 2: Run the Celery Worker (Background Tasks)
This terminal handles the async "Export CSV" functionality and scheduled reminders.

1. Open a new terminal inside the project folder.
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Start the Celery worker targeting the `app.py` instance:
   ```bash
   celery -A backend.app.celery worker --loglevel=info
   ```

*(Note: If you are running Celery Beat for scheduled daily/monthly reports, you can optionally append `-B` to the above command like this: `celery -A backend.app.celery worker -B --loglevel=info`)*

## Default Login Credentials
- **Admin**: `admin@iitm.ac.in` / `adminpassword`
- **Company**: `hr@techcorp.com` / `password123`
- **Student**: `student@iitm.ac.in` / `password123`
