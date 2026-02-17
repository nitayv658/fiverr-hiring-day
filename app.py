import os
import string
import random
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://user:password@localhost:5432/fiverr_test'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============ MODELS ============

class Link(db.Model):
    __tablename__ = 'links'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.String(255), nullable=False)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    click_count = db.Column(db.Integer, default=0)
    credits_earned = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('seller_id', 'original_url', name='uq_seller_url'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'short_url': f'http://localhost:5000/link/{self.short_code}',
            'click_count': self.click_count,
            'credits_earned': float(self.credits_earned),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Click(db.Model):
    __tablename__ = 'clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('links.id'), nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    reward_status = db.Column(db.String(20), default='pending')

class Reward(db.Model):
    __tablename__ = 'rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.String(255), nullable=False, index=True)
    link_id = db.Column(db.Integer, db.ForeignKey('links.id'), nullable=False)
    click_id = db.Column(db.Integer, db.ForeignKey('clicks.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    aws_transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)

# ============ UTILITY FUNCTIONS ============

def generate_short_code(length=8):
    """Generate unique alphanumeric short code"""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not Link.query.filter_by(short_code=code).first():
            return code

def get_client_ip(request):
    """Extract client IP from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def process_reward_async(click_id, seller_id, link_id, amount):
    """Process reward asynchronously without blocking the redirect.

    Runs inside an application context so background threads can use
    Flask-SQLAlchemy safely (fixes test and runtime "working outside
    of application context" errors).
    """
    try:
        with app.app_context():
            # If AWS Bedrock crediting endpoint and bearer token are configured,
            # call it. Otherwise fall back to a local mock delay.
            bedrock_url = os.getenv('BEDROCK_CREDIT_URL')
            bedrock_token = os.getenv('BEDROCK_BEARER_TOKEN')

            aws_txn_id = None
            remote_status = 'completed'

            if bedrock_url and bedrock_token:
                try:
                    import requests

                    headers = {
                        'Authorization': f'Bearer {bedrock_token}',
                        'Content-Type': 'application/json'
                    }
                    payload = {
                        'seller_id': seller_id,
                        'amount': float(amount),
                        'link_id': link_id,
                        'click_id': click_id
                    }
                    resp = requests.post(bedrock_url, json=payload, headers=headers, timeout=5)
                    if resp.status_code >= 200 and resp.status_code < 300:
                        # Expecting JSON { "transaction_id": "..." } or similar
                        try:
                            resp_json = resp.json()
                            aws_txn_id = resp_json.get('transaction_id') or resp_json.get('transactionId')
                        except Exception:
                            aws_txn_id = None
                        remote_status = 'completed'
                    else:
                        remote_status = 'failed'
                except Exception as e:
                    print(f'Bedrock call failed: {e}')
                    remote_status = 'failed'
            else:
                # Local mock of external call latency
                time.sleep(0.05)

            # Persist a Reward record and update related rows regardless of remote outcome
            reward = Reward(
                seller_id=seller_id,
                link_id=link_id,
                click_id=click_id,
                amount=amount,
                status=remote_status,
                aws_transaction_id=aws_txn_id
            )
            db.session.add(reward)

            # Update click reward status
            click = Click.query.get(click_id)
            if click:
                click.reward_status = remote_status

            # Update link credits only on completed
            link = Link.query.get(link_id)
            if link and remote_status == 'completed':
                link.credits_earned = float(link.credits_earned) + float(amount)

            db.session.commit()
    except Exception as e:
        print(f"Reward processing error: {e}")
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            # If rollback also fails, there's not much we can do in a background thread
            pass

# ============ ROUTES ============

@app.route('/health', methods=['GET'])
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

@app.route('/', methods=['GET'])
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

@app.route('/link', methods=['POST'])
def create_link():
    """
    POST /link
    Create a short link for a gig URL
    
    Request:
    {
        "seller_id": "seller123",
        "original_url": "https://fiverr.com/gigs/..."
    }
    
    Response:
    {
        "id": 1,
        "short_url": "http://localhost:5000/link/abc123def",
        "original_url": "https://fiverr.com/gigs/...",
        ...
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('seller_id') or not data.get('original_url'):
            return jsonify({
                'error': 'Missing required fields: seller_id and original_url'
            }), 400
        
        seller_id = data['seller_id'].strip()
        original_url = data['original_url'].strip()
        
        # Check if this seller already shortened this URL
        existing_link = Link.query.filter_by(
            seller_id=seller_id,
            original_url=original_url
        ).first()
        
        if existing_link:
            return jsonify({
                'message': 'Link already exists (reusing existing short code)',
                'link': existing_link.to_dict()
            }), 200
        
        # Generate unique short code
        short_code = generate_short_code()
        
        # Create new link
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

@app.route('/link/<short_code>', methods=['GET'])
def redirect_link(short_code):
    """
    GET /link/<short_code>
    Redirect to original URL and record click + reward (async, <500ms)
    """
    try:
        # Validate short code
        if not short_code or len(short_code) > 10:
            return jsonify({'error': 'Invalid short code'}), 400
        
        # Find the link
        link = Link.query.filter_by(short_code=short_code).first()
        if not link:
            return jsonify({'error': 'Short link not found'}), 404
        
        # Record the click
        click = Click(
            link_id=link.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get('User-Agent', '')
        )
        
        db.session.add(click)
        db.session.commit()
        
        # Increment click count immediately
        link.click_count += 1
        db.session.commit()
        
        # Enqueue reward processing to Celery (non-blocking). Import locally
        # to avoid circular imports when modules are imported at test collection.
        try:
            from tasks import process_reward_task
            process_reward_task.delay(click.id, link.seller_id, link.id, 0.05)
        except Exception:
            # Fallback: process inline if Celery isn't available or import fails
            process_reward_async(click.id, link.seller_id, link.id, 0.05)
        
        # Return redirect immediately (before reward completes)
        return redirect(link.original_url, code=302)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/state', methods=['GET'])
def get_state():
    """
    GET /state?page=1&limit=10
    Get all generated links with analytics (paginated)
    """
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Validate pagination
        if page < 1 or limit < 1 or limit > 100:
            return jsonify({'error': 'Invalid pagination parameters'}), 400
        
        offset = (page - 1) * limit
        
        # Get total count
        total = Link.query.count()
        
        # Get paginated links
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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='localhost', port=5000, threaded=True)
