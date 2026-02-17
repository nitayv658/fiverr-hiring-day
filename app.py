import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv

load_dotenv()

# Modern SQLAlchemy 3.x Style Base
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'postgresql://user:password@localhost:5432/fiverr_test'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # --- Routes ---

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'api': 'Fiverr Hiring Day API',
            'version': '2.0',
            'endpoints': ['/health', '/messages']
        }), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/messages', methods=['GET'])
    def get_messages():
        messages = db.session.execute(db.select(Message).order_by(Message.created_at)).scalars()
        return jsonify([m.to_dict() for m in messages]), 200

    @app.route('/messages', methods=['POST'])
    def create_message():
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Field "text" is required'}), 400
        
        new_msg = Message(text=data['text'])
        db.session.add(new_msg)
        db.session.commit()
        return jsonify(new_msg.to_dict()), 201

    @app.route('/messages/<int:msg_id>', methods=['GET'])
    def get_message(msg_id):
        message = db.get_or_404(Message, msg_id)
        return jsonify(message.to_dict()), 200

    @app.route('/messages/<int:msg_id>', methods=['GET', 'PUT'])
    def update_message(msg_id):
        message = db.get_or_404(Message, msg_id)
        data = request.get_json()
        
        if 'text' in data:
            message.text = data['text']
            db.session.commit()
            return jsonify(message.to_dict()), 200
            
        return jsonify({'error': 'Nothing to update'}), 400

    @app.route('/messages/<int:msg_id>', methods=['DELETE'])
    def delete_message(msg_id):
        message = db.get_or_404(Message, msg_id)
        db.session.delete(message)
        db.session.commit()
        return jsonify({'message': f'Message {msg_id} deleted'}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='localhost', port=5000)
