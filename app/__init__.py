
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, url_for
from flask_migrate import Migrate
from werkzeug.exceptions import RequestEntityTooLarge

from app.extensions import db, csrf

load_dotenv()

migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Resume upload configuration
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.instance_path, "uploads"
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Application configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Secure session cookie settings
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("FLASK_ENV") == "production"
    )
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing from .env")

    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("DATABASE_URL is missing from .env")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register models and routes
    from app import models
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    # Handle files exceeding the upload limit
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        flash("File size exceeds the 5 MB limit.", "danger")
        return redirect(url_for("main.upload_resume")), 413

    return app
