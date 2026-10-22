from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User

import os
import uuid
import zipfile
from io import BytesIO

from flask import current_app
from werkzeug.utils import secure_filename

main_bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


@main_bp.route("/")
def home():
    return {
        "message": "Resume Analyzer and ATS Feedback Tool",
        "status": "running"
    }


@main_bp.route("/health")
def health():
    return {"status": "healthy"}, 200


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(name) > 100:
            flash("Name must be 100 characters or fewer.", "danger")
            return render_template("register.html")

        if "@" not in email or len(email) > 255:
            flash("Enter a valid email address.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = db.session.scalar(
            select(User).where(User.email == email)
        )
        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.scalar(
            select(User).where(User.email == email)
        )

        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name

        flash("Welcome back!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User")
    )


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_extension(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def valid_resume_content(file_bytes, extension):
    if extension == "pdf":
        return file_bytes.startswith(b"%PDF-")

    if extension == "docx":
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as archive:
                return (
                    archive.testzip() is None
                    and "[Content_Types].xml" in archive.namelist()
                    and "word/document.xml" in archive.namelist()
                )
        except (zipfile.BadZipFile, OSError):
            return False

    return False


@main_bp.route("/upload-resume", methods=["GET", "POST"])
@login_required
def upload_resume():
    if request.method == "GET":
        return render_template("upload_resume.html")

    uploaded_file = request.files.get("resume")

    if uploaded_file is None or not uploaded_file.filename:
        flash("Please select a resume to upload.", "danger")
        return redirect(url_for("main.upload_resume"))

    original_name = secure_filename(uploaded_file.filename)

    if not original_name or not allowed_extension(original_name):
        flash("Only PDF and DOCX files are allowed.", "danger")
        return redirect(url_for("main.upload_resume"))

    extension = original_name.rsplit(".", 1)[1].lower()

    # Read at most 5 MB + 1 byte to enforce the size limit.
    file_bytes = uploaded_file.stream.read(
        current_app.config["MAX_CONTENT_LENGTH"] + 1
    )

    if not file_bytes:
        flash("The selected file is empty.", "danger")
        return redirect(url_for("main.upload_resume"))

    if len(file_bytes) > current_app.config["MAX_CONTENT_LENGTH"]:
        flash("Resume must be 5 MB or smaller.", "danger")
        return redirect(url_for("main.upload_resume"))

    if not valid_resume_content(file_bytes, extension):
        flash(
            "The file content does not match a valid PDF or DOCX file.",
            "danger",
        )
        return redirect(url_for("main.upload_resume"))

    # Generate a server-side filename instead of trusting user input.
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    upload_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], stored_name
    )

    try:
        with open(upload_path, "xb") as destination:
            destination.write(file_bytes)
    except OSError:
        current_app.logger.exception("Resume upload failed.")
        flash("Unable to save the resume. Please try again.", "danger")
        return redirect(url_for("main.upload_resume"))

    flash("Resume uploaded and validated successfully.", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.errorhandler(413)
def upload_too_large(error):
    flash("Resume must be 5 MB or smaller.", "danger")
    return redirect(url_for("main.upload_resume"))
