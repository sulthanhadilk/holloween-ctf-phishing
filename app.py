import os
import re
import uuid
import logging
import sqlite3
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, abort, jsonify,
    send_from_directory
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Regexp
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

# ─── App Configuration ────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))
app.config["WTF_CSRF_ENABLED"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DATABASE = os.path.join(app.root_path, "registrations.db")

ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    generate_password_hash("changeme_before_production"),
)

csrf = CSRFProtect(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Database Helpers ─────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL;")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            phone       TEXT    NOT NULL,
            photo_path  TEXT,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def sanitize_text(value: str) -> str:
    """Strip leading/trailing whitespace; collapse internal spaces."""
    return " ".join(value.strip().split())


def validate_phone(phone: str) -> bool:
    """Accept E.164 or common local formats (7–15 digits, optional +/spaces/dashes)."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.fullmatch(r"\+?\d{7,15}", cleaned))


# ─── WTForms Form ─────────────────────────────────────────────────────────────
class RegistrationForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    email = StringField(
        "Gmail Address",
        validators=[
            DataRequired(),
            Email(),
            Regexp(
                r"^[^@]+@gmail\.com$",
                message="Please enter a valid @gmail.com address.",
            ),
        ],
    )
    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(min=7, max=20)],
    )
    photo = FileField("Photo (optional)")
    consent = BooleanField(
        "I consent",
        validators=[DataRequired(message="You must accept the consent agreement to register.")],
    )


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    form = RegistrationForm()
    if form.validate_on_submit():
        full_name = sanitize_text(form.full_name.data)
        email = form.email.data.strip().lower()
        phone = sanitize_text(form.phone.data)

        if not validate_phone(phone):
            flash("Please enter a valid phone number (7–15 digits).", "error")
            return render_template("index.html", form=form)

        # Optional local photo upload
        photo_path = None
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            if not allowed_file(photo_file.filename):
                flash("Only JPG, JPEG, PNG, or WEBP images are allowed.", "error")
                return render_template("index.html", form=form)
            ext = photo_file.filename.rsplit(".", 1)[1].lower()
            safe_name = f"{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            photo_file.save(save_path)
            photo_path = safe_name

        db = get_db()
        try:
            db.execute(
                "INSERT INTO registrations (full_name, email, phone, photo_path) VALUES (?, ?, ?, ?)",
                (full_name, email, phone, photo_path),
            )
            db.commit()
            logger.info("New registration: %s <%s>", full_name, email)
            flash("🎃 You're registered! Prepare yourself for the NIGHTMARE CTF.", "success")
            return redirect(url_for("success"))
        except sqlite3.IntegrityError:
            flash("This email is already registered. Each contestant may only register once.", "error")
            return render_template("index.html", form=form)
        except Exception as exc:
            logger.exception("Registration error: %s", exc)
            flash("An unexpected error occurred. Please try again.", "error")
            return render_template("index.html", form=form)

    return render_template("index.html", form=form)


@app.route("/success")
def success():
    return render_template("success.html")


# ─── Admin (protected) ────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            session.permanent = False
            return redirect(url_for("admin_list"))
        flash("Invalid password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/registrations")
@admin_required
def admin_list():
    db = get_db()
    rows = db.execute(
        "SELECT id, full_name, email, phone, photo_path, registered_at FROM registrations ORDER BY registered_at DESC"
    ).fetchall()
    return render_template("admin_list.html", rows=rows)


@app.route("/admin/uploads/<path:filename>")
@admin_required
def admin_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ─── Error Handlers ───────────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    flash("Uploaded file is too large. Maximum size is 5 MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("500 error")
    return render_template("500.html"), 500


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
