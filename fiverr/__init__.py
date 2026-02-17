from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()


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
