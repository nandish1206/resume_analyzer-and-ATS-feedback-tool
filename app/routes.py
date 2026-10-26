
import os
import re
import uuid
from functools import wraps
from flask import session
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
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
from app.models import User, AnalysisHistory
from app.utils.text_extraction import (
    extract_resume_text,
    ResumeExtractionError,
)
from app.utils.resume_analysis import (
    analyze_resume,
    ResumeAnalysisError,
)
from app.utils.score_calculator import (
    calculate_resume_match_score,
    get_score_label,
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
    latest_analysis = db.session.execute(
        select(AnalysisHistory)
        .where(
            AnalysisHistory.user_id == session["user_id"],
            AnalysisHistory.status == "completed",
        )
        .order_by(AnalysisHistory.created_at.desc())
    ).scalars().first()

    match_score = None
    score_label = None
    ats_score = None
    match_percentage = None

    if latest_analysis and latest_analysis.analysis_result:
        result = latest_analysis.analysis_result
        match_score = result.get("overall_match_score")
        ats_score = result.get("ats_score")
        match_percentage = result.get("match_percentage")

        if match_score is not None:
            score_label = get_score_label(match_score)

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", ""),
        match_score=match_score,
        score_label=score_label,
        ats_score=ats_score,
        match_percentage=match_percentage,
    )


@main_bp.route("/history")
@login_required
def history():
    analyses = db.session.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.user_id == session["user_id"])
        .order_by(AnalysisHistory.created_at.desc())
    ).scalars().all()

    return render_template(
        "history.html",
        analyses=analyses,
    )

@main_bp.route("/history/<int:analysis_id>")
@login_required
def view_analysis_history(analysis_id):
    analysis = db.session.scalar(
        select(AnalysisHistory).where(
            AnalysisHistory.id == analysis_id,
            AnalysisHistory.user_id == session["user_id"],
        )
    )

    if analysis is None:
        flash("Analysis not found.", "warning")
        return redirect(url_for("main.history"))

    result = analysis.analysis_result or {}
    match_score = result.get("overall_match_score")

    score_label = (
        get_score_label(match_score)
        if match_score is not None
        else "Not available"
    )

    return render_template(
        "analysis_result.html",
        result=result,
        match_score=match_score,
        score_label=score_label,
        target_role=analysis.target_role,
        analysis_id=analysis.id,
        completed_suggestions=analysis.completed_suggestions or [],
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

        session["resume_stored_filename"] = stored_filename
        session["uploaded_filename"] = original_filename

        flash(
            "Resume uploaded successfully. Now enter your job details.",
            "success",
        )
        return redirect(url_for("main.job_details"))

    return render_template("upload.html")




@main_bp.route("/job-details", methods=["GET", "POST"])
@login_required
def job_details():
    target_role = session.get("target_role", "")
    job_description = session.get("job_description", "")

    if request.method == "GET":
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        )

    target_role = request.form.get("target_role", "").strip()
    job_description = request.form.get("job_description", "").strip()

    if not target_role and not job_description:
        flash(
            "Enter a target job role, a job description, or both.",
            "danger",
        )
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        ), 400

    if len(target_role) > 150:
        flash("Target job role must not exceed 150 characters.", "danger")
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        ), 400

    if len(job_description) > 15000:
        flash(
            "Job description must not exceed 15,000 characters.",
            "danger",
        )
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        ), 400

    stored_filename = session.get("resume_stored_filename")

    if not stored_filename:
        flash("Please upload your resume first.", "warning")
        return redirect(url_for("main.upload_resume"))

    if (
        os.path.basename(stored_filename) != stored_filename
        or not stored_filename.lower().endswith((".pdf", ".docx"))
    ):
        session.pop("resume_stored_filename", None)
        flash("Invalid resume reference. Please upload again.", "danger")
        return redirect(url_for("main.upload_resume"))

    upload_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        stored_filename,
    )

    if not os.path.isfile(upload_path):
        session.pop("resume_stored_filename", None)
        flash("Resume not found. Please upload it again.", "danger")
        return redirect(url_for("main.upload_resume"))

    # Preserve submitted values if analysis fails.
    session["target_role"] = target_role
    session["job_description"] = job_description

    try:
        resume_text = extract_resume_text(upload_path)

        result = analyze_resume(
            resume_text=resume_text,
            target_role=target_role,
            job_description=job_description,
        )

        match_score = calculate_resume_match_score(result)
        score_label = get_score_label(match_score)

        result["overall_match_score"] = match_score

        analysis = AnalysisHistory(
            user_id=session["user_id"],
            target_role=target_role or None,
            ats_score=result["ats_score"],
            status="completed",
            analysis_result=result,
        )

        db.session.add(analysis)
        db.session.commit()

    except ResumeExtractionError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("main.upload_resume"))

    except (ResumeAnalysisError, ValueError) as exc:
        db.session.rollback()
        current_app.logger.warning("Resume analysis failed: %s", exc)
        flash(
            "Analysis failed or timed out. Please try again.",
            "danger",
        )
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        ), 502

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unable to save resume analysis.")
        flash(
            "Unable to save the analysis. Please try again.",
            "danger",
        )
        return render_template(
            "job_details.html",
            target_role=target_role,
            job_description=job_description,
        ), 500

    return render_template(
        "analysis_result.html",
        result=result,
        match_score=match_score,
        score_label=score_label,
        target_role=target_role,
        analysis_id=analysis.id,
        completed_suggestions=analysis.completed_suggestions or [],
    )


@main_bp.route(
    "/analysis/<int:analysis_id>/checklist",
    methods=["POST"],
)
@login_required
def update_improvement_checklist(analysis_id):
    analysis = db.session.scalar(
        select(AnalysisHistory).where(
            AnalysisHistory.id == analysis_id,
            AnalysisHistory.user_id == session["user_id"],
        )
    )

    if analysis is None:
        return jsonify({"error": "Analysis not found."}), 404

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request data."}), 400

    completed = payload.get("completed_suggestions")

    if not isinstance(completed, list):
        return jsonify({"error": "Invalid checklist data."}), 400

    result = analysis.analysis_result or {}
    suggestions = result.get("improvement_suggestions", [])

    if not isinstance(suggestions, list):
        return jsonify({"error": "Invalid analysis suggestions."}), 400

    # Accept only valid suggestion indexes.
    if any(
        type(index) is not int or index < 0 or index >= len(suggestions)
        for index in completed
    ):
        return jsonify({"error": "Invalid suggestion index."}), 400

    try:
        analysis.completed_suggestions = sorted(set(completed))
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Unable to save improvement checklist."
        )
        return jsonify({"error": "Unable to save checklist progress."}), 500

    return jsonify({
        "success": True,
        "completed_suggestions": analysis.completed_suggestions,
    }), 200


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
