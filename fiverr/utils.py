import secrets
from fiverr.models import Link


def generate_short_code(length=6):
    """Generate a cryptographically secure unique short code."""
    while True:
        code = secrets.token_urlsafe(length)[:8]
        if not Link.query.filter_by(short_code=code).first():
            return code


def get_client_ip(req):
    """Extract client IP from request."""
    if req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For').split(',')[0]
    return req.remote_addr
