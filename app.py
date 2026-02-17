"""Backward-compatibility entry point.

Imports from this module (app, db, Link, Click, Reward) continue to work
so that tasks.py, test_api.py, and ``FLASK_APP=app.py`` all function
without modification.

The real application code lives in the ``fiverr`` package.
"""
from fiverr import create_app, db
from fiverr.models import Link, Click, Reward

app = create_app()

__all__ = ['app', 'db', 'Link', 'Click', 'Reward']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='localhost', port=5000, threaded=True)
