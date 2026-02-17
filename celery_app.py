import os
import sys


class _DummyCelery:
    """Lightweight Celery stub for tests: tasks run synchronously via `.delay()`.

    This avoids importing heavy Celery/Kombu dependencies during pytest
    collection and speeds up tests.
    """
    def __init__(self, *args, **kwargs):
        self.conf = {}

    def task(self, *dargs, **dkwargs):
        def decorator(fn):
            # Attach a `.delay()` that executes the task synchronously.
            def delay(*args, **kwargs):
                return fn(*args, **kwargs)
            fn.delay = delay
            return fn
        return decorator

    def __getattr__(self, name):
        # Provide no-op attributes for compatibility
        def _noop(*args, **kwargs):
            return None
        return _noop


def make_celery(app_name=__name__):
    # If running inside pytest (or explicitly flagged), return a dummy
    # synchronous Celery implementation to speed up tests and avoid
    # requiring a running broker during unit tests.
    if os.getenv('UNIT_TEST') == '1' or 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST'):
        return _DummyCelery()

    try:
        from celery import Celery
    except Exception:
        # Fallback to dummy if Celery isn't available
        return _DummyCelery()

    broker = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    backend = os.getenv('CELERY_RESULT_BACKEND', broker)
    celery = Celery(app_name, broker=broker, backend=backend)
    celery.conf.update(task_track_started=True)
    return celery


celery = make_celery()
