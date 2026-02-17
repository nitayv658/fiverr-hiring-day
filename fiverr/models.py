from datetime import datetime, timezone
from fiverr import db


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
