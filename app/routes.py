
import os
import re
import uuid
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import User
from app.utils.text_extraction import (
    extract_resume_text,
    ResumeExtractionError,
)

main_bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@main_bp.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm_password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(name) > 100:
            flash("Name must be at most 100 characters.", "danger")
            return render_template("register.html")

        if (
            len(email) > 255
            or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        ):
            flash("Enter a valid email address.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger",
            )
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        existing_user = db.session.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            flash(
                "An account with this email already exists.",
                "danger",
            )
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(
                "An account with this email already exists.",
                "danger",
            )
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
        session.permanent = True
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
        user_name=session.get("user_name", "User"),
    )


@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_resume():
    if request.method == "POST":
        if "resume" not in request.files:
            flash("Please select a resume file.", "danger")
            return redirect(url_for("main.upload_resume"))

        file = request.files["resume"]

        if not file.filename or not file.filename.strip():
            flash("Please select a file to upload.", "danger")
            return redirect(url_for("main.upload_resume"))

        if not allowed_file(file.filename):
            flash("Only PDF and DOCX files are allowed.", "danger")
            return redirect(url_for("main.upload_resume"))

        original_filename = secure_filename(file.filename)

        if not original_filename:
            flash("Invalid filename.", "danger")
            return redirect(url_for("main.upload_resume"))

        extension = original_filename.rsplit(".", 1)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}.{extension}"

        upload_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            stored_filename,
        )

        try:
            file.save(upload_path)
            extracted_text = extract_resume_text(upload_path)

        except ResumeExtractionError as exc:
            if os.path.exists(upload_path):
                os.remove(upload_path)

            flash(str(exc), "danger")
            return redirect(url_for("main.upload_resume"))

        except OSError:
            current_app.logger.exception(
                "Unable to save or read the uploaded resume."
            )

            if os.path.exists(upload_path):
                os.remove(upload_path)

            flash(
                "Unable to save or read the file. Please try again.",
                "danger",
            )
            return redirect(url_for("main.upload_resume"))

        flash("Resume uploaded and text extracted successfully.", "success")

        return render_template(
            "upload.html",
            extracted_text=extracted_text,
            uploaded_filename=original_filename,
        )

    return render_template("upload.html")


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
