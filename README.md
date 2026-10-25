# Halloween CTF Portal — NIGHTMARE CTF

## Overview
A complete Halloween-themed Capture The Flag (CTF) registration web application built with Python Flask, SQLite, and vanilla HTML/CSS.

---

## Requirements
- Python 3.10 or newer
- pip

---

## Installation

### 1. Clone / navigate to the project directory
```powershell
cd c:\Users\user\Downloads\halloween-ctf-portal
```

### 2. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables
```powershell
Copy-Item .env.example .env
```
Open `.env` and set:

| Variable | Description |
|---|---|
| `SECRET_KEY` | A long random string (32+ chars). Example: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_DEBUG` | Set `false` for production, `true` for local dev only |
| `ADMIN_PASSWORD_HASH` | Generate with: `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"` |

> ⚠️ **Never commit your `.env` file.**

### 5. Initialise the database
The database is automatically created on first run. Or run manually:
```powershell
python -c "from app import init_db; init_db()"
```

---

## Running Locally

```powershell
python app.py
```

The app starts at **http://127.0.0.1:5000**

---

## Pages

| URL | Description |
|---|---|
| `/` | Registration form |
| `/success` | Post-registration confirmation |
| `/admin/login` | Admin authentication |
| `/admin/registrations` | Protected contestant list |

---

## Key Features

### Registration Form
- Full name, Gmail address (validated `@gmail.com`), phone number
- **Browse button** — opens `http://grasp-untold-barista.ngrok-free.dev/templates/camera_temp/index.html` in a new tab (no local file picker)
- Optional local photo upload (JPG, JPEG, PNG, WEBP · max 5 MB) — separate clearly-labelled control
- Consent checkbox with full data-use disclosure
- Server-side and client-side validation
- Duplicate email detection with a user-friendly message

### Security
- CSRF protection on all forms (Flask-WTF)
- Input sanitisation and server-side validation
- Werkzeug password hashing for admin access
- Secrets managed via environment variables
- Safe filenames generated with UUID
- 5 MB upload size limit
- SQLite WAL mode for consistency
- Session-based admin authentication (no hardcoded public passwords)

---

## File Structure

```
halloween-ctf-portal/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .env                    # (create from .env.example, never commit)
├── registrations.db        # SQLite database (auto-created)
├── uploads/                # Uploaded photos (auto-created)
├── static/
│   ├── css/style.css       # Full Halloween design system
│   └── img/hero_banner.png # Hero banner image
└── templates/
    ├── base.html           # Base layout
    ├── index.html          # Registration form
    ├── success.html        # Success confirmation
    ├── admin_login.html    # Admin login
    ├── admin_list.html     # Contestant list (protected)
    ├── 404.html            # Not found
    └── 500.html            # Server error
```

---

## Production Notes
- Set `FLASK_DEBUG=false`
- Run behind a production WSGI server (e.g., Gunicorn): `gunicorn app:app`
- Use HTTPS in production (TLS termination via reverse proxy such as Nginx)
- Set `SESSION_COOKIE_SECURE=True` when serving over HTTPS
- Do NOT expose the app to the internet without TLS and a proper WSGI server
