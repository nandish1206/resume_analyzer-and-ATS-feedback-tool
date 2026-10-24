
import os

from dotenv import load_dotenv
from flask import Flask

from app.extensions import db, csrf

load_dotenv()


def create_app():
    app = Flask(__name__)

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

    db.init_app(app)
    csrf.init_app(app)

    from app import models
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
