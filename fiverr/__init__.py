import logging

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def _init_redis(app):
    """Create a Redis client and store it on the app.

    Returns None (and logs a warning) when Redis is unavailable so the
    application degrades gracefully to DB-only lookups.
    """
    try:
        import redis
        client = redis.Redis.from_url(
            app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True,
            socket_connect_timeout=1,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.warning("Redis unavailable, caching disabled: %s", exc)
        return None


def create_app(config_overrides=None):
    """Application factory.

    Args:
        config_overrides: dict of config keys to override (used by tests).
    Returns:
        Configured Flask application with all extensions and blueprints.
    """
    app = Flask(__name__)

    # Load config — imported lazily to avoid circular imports.
    from fiverr.config import Config
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    # Initialise Redis (graceful degradation if unavailable).
    app.extensions['redis'] = _init_redis(app)

    # Register blueprint — imported lazily to avoid circular imports.
    from fiverr.routes import api_bp
    app.register_blueprint(api_bp)

    # App-wide error handlers (blueprint-level 404 doesn't catch unknown URLs).
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    return app
