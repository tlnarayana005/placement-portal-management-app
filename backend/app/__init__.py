from flask import Flask, render_template
from flask_jwt_extended import jwt_required

from .config import Config
from .extensions import db, init_redis_app, jwt


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    init_redis_app(app)

    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.company import company_bp
    from .routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    # Health check endpoint
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # Single-page UI entry point (served via CDN-loaded Vue)
    @app.get("/")
    def index():
        return render_template("index.html")

    return app

