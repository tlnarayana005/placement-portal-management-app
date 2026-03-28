import os

from flask import Flask
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User


def seed_admin():
    app: Flask = create_app()
    with app.app_context():
        db.create_all()

        admin_email = os.getenv("ADMIN_EMAIL", "admin@ppa.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        existing = User.query.filter_by(email=admin_email.lower(), role="admin").first()
        if existing:
            return {"seeded": True, "reason": "admin already exists"}

        user = User(
            role="admin",
            email=admin_email.lower(),
            password_hash=generate_password_hash(admin_password),
            is_active=True,
            is_blacklisted=False,
        )
        db.session.add(user)
        db.session.commit()
        return {"seeded": True}


if __name__ == "__main__":
    print(seed_admin())

