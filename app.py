from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/fiverr_test')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a simple model
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'message': 'API and database connection working!',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Hello World endpoint
@app.route('/', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World! Fiverr Hiring Day API'}), 200

# Create a message
@app.route('/messages', methods=['POST'])
def create_message():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing required field: text'}), 400
        
        message = Message(text=data['text'])
        db.session.add(message)
        db.session.commit()
        
        return jsonify(message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all messages
@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        messages = Message.query.all()
        return jsonify([msg.to_dict() for msg in messages]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get a specific message
@app.route('/messages/<int:id>', methods=['GET'])
def get_message(id):
    try:
        message = Message.query.get_or_404(id)
        return jsonify(message.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Delete a message
@app.route('/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    try:
        message = Message.query.get_or_404(id)
        db.session.delete(message)
        db.session.commit()
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='localhost', port=5000)
