import string
import random
from fiverr.models import Link


def generate_short_code(length=8):
    """Generate unique alphanumeric short code."""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not Link.query.filter_by(short_code=code).first():
            return code


def get_client_ip(req):
    """Extract client IP from request."""
    if req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For').split(',')[0]
    return req.remote_addr
