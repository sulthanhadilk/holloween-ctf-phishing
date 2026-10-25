import os
import re
import logging

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Regexp
from dotenv import load_dotenv

load_dotenv()

# ─── App Configuration ────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))
app.config["WTF_CSRF_ENABLED"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

csrf = CSRFProtect(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        phone = sanitize_text(form.phone.data)

        if not validate_phone(phone):
            flash("Please enter a valid phone number (7–15 digits).", "error")
            return render_template("index.html", form=form)

        # Validate the optional file without persisting it.
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            if not allowed_file(photo_file.filename):
                flash("Only JPG, JPEG, PNG, or WEBP images are allowed.", "error")
                return render_template("index.html", form=form)

        logger.info("Demo submission validated without persistence")
        flash(
            "🎃 Demo submission accepted. No personal data or photos are stored.",
            "success",
        )
        return redirect(url_for("success"))

    return render_template("index.html", form=form)


@app.route("/success")
def success():
    return render_template("success.html")


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
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
