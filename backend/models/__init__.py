"""
Database extensions and shared components for the Placement Portal.

Extensions (db, jwt, cache) are created here as unbound instances and
bound to the Flask app via init_app() in backend/app.py.
Models are defined in models/models.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
