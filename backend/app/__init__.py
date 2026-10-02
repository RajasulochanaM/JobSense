"""JobSense Flask application factory."""
import logging

from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from .config.settings import Config
from .database import db
from .utils.responses import APIError, error, success


def configure_logging(level):
    logging.basicConfig(
        level=getattr(logging, str(level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # Keep third-party noise down; never log request bodies (passwords, resumes).
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def register_error_handlers(app):
    logger = logging.getLogger("jobsense.errors")

    @app.errorhandler(APIError)
    def handle_api_error(exc):
        if exc.status >= 500:
            logger.error("API error %s: %s", exc.code, exc.message)
        return error(exc.message, exc.code, exc.status, exc.details)

    @app.errorhandler(db.DatabaseError)
    def handle_db_error(exc):
        logger.error("Database failure: %s", exc)
        return error("A database error occurred. Please try again later.", "DATABASE_ERROR", 503)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_exc):
        return error(f"File is too large. Maximum size is {app.config['MAX_RESUME_SIZE_MB']} MB.",
                     "FILE_TOO_LARGE", 413)

    @app.errorhandler(HTTPException)
    def handle_http(exc):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 400: "BAD_REQUEST"}
        message = "The requested resource was not found." if exc.code == 404 else exc.description
        return error(message, codes.get(exc.code, "HTTP_ERROR"), exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        # Full details go to the server log only - never to the client.
        logger.exception("Unhandled error: %s", exc)
        return error("An unexpected error occurred.", "INTERNAL_ERROR", 500)


def register_blueprints(app):
    from .routes import (admin_routes, auth_routes, career_routes, job_routes, match_routes, profile_routes,
                         resume_routes, tracking_routes)
    for module in (auth_routes, profile_routes, resume_routes, job_routes, match_routes, tracking_routes,
                   career_routes, admin_routes):
        app.register_blueprint(module.bp)


def register_cli(app):
    from .cli import create_admin, init_db_command

    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    configure_logging(app.config["LOG_LEVEL"])
    log = logging.getLogger("jobsense")

    if app.config["ENV"] == "production" and app.config["SECRET_KEY"].startswith("dev-only"):
        log.warning("SECRET_KEY is not set - configure it before running in production")

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
         allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         max_age=600)

    db.init_db(app.config)
    register_blueprints(app)
    register_error_handlers(app)
    register_cli(app)

    @app.get("/api/health")
    def health():
        from .services.job_service import provider_info
        return success({"status": "ok", "database": db.ping(), "job_provider": provider_info()})

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    with app.app_context():
        from .database.migrations import apply_migrations
        apply_migrations()
        from .services.job_service import provider_info
        info = provider_info()
        log.info("JobSense API started (env=%s, job provider=%s%s)", app.config["ENV"], info["provider"],
                 " [MOCK DATA]" if info["is_mock"] else "")
    return app
