
import re
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User

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


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
