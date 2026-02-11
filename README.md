# Fiverr Hiring Day API

A simple "Hello World" API project with Python, Flask, and PostgreSQL for the Fiverr accelerated hiring day.

## Requirements

- Python 3.8+
- PostgreSQL 12+ (local installation or Docker)
- Git

## Setup Instructions

### 1. Clone or Navigate to Project
```bash
cd /Users/nitay658/Documents/Projects/Fiverr-project
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

#### Option A: Using Docker (Recommended)
```bash
docker run --name fiverr-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=fiverr_test \
  -p 5432:5432 \
  -d postgres:15
```

#### Option B: Local PostgreSQL Installation
```bash
# On macOS with Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb fiverr_test

# Create user (if needed)
psql -U postgres
CREATE USER user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE fiverr_test TO user;
```

### 5. Configure Environment
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your database credentials if different
# DATABASE_URL=postgresql://user:password@localhost:5432/fiverr_test
```

### 6. Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```
Response: Database connection status

### Hello World
```
GET /
```
Response: `{"message": "Hello World! Fiverr Hiring Day API"}`

### Create Message
```
POST /messages
Content-Type: application/json

{"text": "Your message here"}
```

### Get All Messages
```
GET /messages
```

### Get Specific Message
```
GET /messages/<id>
```

### Delete Message
```
DELETE /messages/<id>
```

## Testing with cURL or Postman

```bash
# Test health check
curl http://localhost:5000/health

# Test hello world
curl http://localhost:5000/

# Create a message
curl -X POST http://localhost:5000/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello Fiverr!"}'

# Get all messages
curl http://localhost:5000/messages
```

## Project Structure
```
Fiverr-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Notes
- Ensure PostgreSQL is running before starting the API
- The database tables will be created automatically on first run
- Check the health endpoint to verify the connection is working
