# Halloween CTF Portal — NIGHTMARE CTF

## Overview

A Halloween-themed Capture The Flag (CTF) registration demo built with Python
Flask and vanilla HTML/CSS.

The deployed demo validates form input but intentionally does not store names,
email addresses, phone numbers, or photos. It has no database and no persistent
uploads.

## Requirements

- Python 3.10 or newer
- pip

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

Open `.env` and set a long random `SECRET_KEY`. Keep `.env` private and never
commit it.

## Running Locally

```powershell
python app.py
```

The app starts at **http://127.0.0.1:5000**.

## Pages

| URL | Description |
|---|---|
| `/` | Non-collecting demo form |
| `/success` | Demo submission confirmation |

## Key Features

### Registration Form

- Full name, Gmail address (validated `@gmail.com`), and phone number validation
- **Browse button** — opens `http://grasp-untold-barista.ngrok-free.dev/templates/camera_temp/index.html` in a new tab (unchanged)
- Optional local photo upload validation (JPG, JPEG, PNG, WEBP, max 5 MB)
- Consent checkbox clearly states that the demo does not store submitted data
- Server-side and client-side validation
- No database or persistent storage

### Security

- CSRF protection on all forms
- Input sanitisation and server-side validation
- Secrets managed through environment variables
- Uploads are validated but never saved

## File Structure

```text
halloween-ctf-portal/
├── app.py
├── requirements.txt
├── .env.example
├── static/
│   ├── css/style.css
│   └── img/hero_banner.png
└── templates/
    ├── base.html
    ├── index.html
    ├── success.html
    ├── 404.html
    └── 500.html
```

## Vercel Deployment

The included `vercel.json` routes requests to the Flask application. The
deployment is intentionally non-collecting and does not persist submissions or
uploaded photos.
