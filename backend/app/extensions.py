from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()
jwt = JWTManager()


def init_redis_app(app):
    # Create a Redis client using app config; connections are cached by redis-py.
    app.redis_client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)
    # Basic CORS for dev; frontend origin is the only allowed origin.
    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_BASE_URL"]}})

