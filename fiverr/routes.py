import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, redirect
from sqlalchemy import text
from fiverr import db
from fiverr.models import Link, Click
from fiverr.utils import generate_short_code, get_client_ip

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'message': 'API and database connection working!',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@api_bp.route('/', methods=['GET'])
def index():
    return jsonify({
        'api': 'Fiverr Shareable Links API',
        'version': '1.0',
        'endpoints': {
            'POST /link': 'Create a short link',
            'GET /link/<short_code>': 'Redirect to original URL and reward seller',
            'GET /state': 'Get analytics (paginated)'
        }
    }), 200


@api_bp.route('/link', methods=['POST'])
def create_link():
    """
    POST /link
    Create a short link for a gig URL
    """
    try:
        data = request.get_json()

        if not data or not data.get('seller_id') or not data.get('original_url'):
            return jsonify({
                'error': 'Missing required fields: seller_id and original_url'
            }), 400

        seller_id = data['seller_id'].strip()
        original_url = data['original_url'].strip()

        existing_link = Link.query.filter_by(
            seller_id=seller_id,
            original_url=original_url
        ).first()

        if existing_link:
            return jsonify({
                'message': 'Link already exists (reusing existing short code)',
                'link': existing_link.to_dict()
            }), 200

        short_code = generate_short_code()

        link = Link(
            seller_id=seller_id,
            original_url=original_url,
            short_code=short_code
        )

        db.session.add(link)
        db.session.commit()

        return jsonify({
            'message': 'Short link created successfully',
            'link': link.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/link/<short_code>', methods=['GET'])
def redirect_link(short_code):
    """
    GET /link/<short_code>
    Redirect to original URL and record click + reward (async, <500ms)
    """
    try:
        if not short_code or len(short_code) > 10:
            return jsonify({'error': 'Invalid short code'}), 400

        link = Link.query.filter_by(short_code=short_code).first()
        if not link:
            return jsonify({'error': 'Short link not found'}), 404

        click = Click(
            link_id=link.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get('User-Agent', '')
        )

        db.session.add(click)
        db.session.commit()

        link.click_count += 1
        db.session.commit()

        # Enqueue reward processing to Celery (non-blocking).
        # Import locally to avoid circular imports.
        try:
            from tasks import process_reward_task
            process_reward_task.delay(click.id, link.seller_id, link.id, 0.05)
        except Exception as e:
            logger.warning("Reward enqueue failed: %s", e)

        return redirect(link.original_url, code=302)

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/state', methods=['GET'])
def get_state():
    """
    GET /state?page=1&limit=10
    Get all generated links with analytics (paginated)
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)

        if page < 1 or limit < 1 or limit > 100:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        offset = (page - 1) * limit

        total = Link.query.count()
        links = Link.query.order_by(Link.created_at.desc()).limit(limit).offset(offset).all()

        return jsonify({
            'data': [link.to_dict() for link in links],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
