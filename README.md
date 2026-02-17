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

---

## Testing Instructions (Gemini)

To test your **Fiverr Shareable Links API**, you need to verify three things: the database connection, the link generation logic, and the asynchronous reward system.

Follow these instructions in order to ensure everything is functioning correctly.

### Phase 1: Environment Readiness

Before running tests, ensure your local environment is active and the database is initialized.

1. **Activate Venv:** `source venv/bin/activate`
2. **Set Environment Variables:** Ensure your `.env` file has a valid `DATABASE_URL`.
3. **Run the App:**
```bash
python app.py

```

*Note: The script will automatically run `db.create_all()` and create your PostgreSQL tables on startup.*

### Phase 2: Manual Testing (The "Happy Path")

#### 1. Verify API Connectivity

Check that the server is alive and the database connection is healthy.

```bash
curl -i http://localhost:5000/health

```

* **Success Criteria:** Status `200 OK` and `{"status": "healthy"}`.

#### 2. Create a Short Link

Generate a link for a seller.

```bash
curl -X POST http://localhost:5000/link \
   -H "Content-Type: application/json" \
   -d '{"seller_id": "seller_abc", "original_url": "https://fiverr.com/test-gig"}'

```

* **Success Criteria:** Status `201 Created`. **Copy the `short_code`** from the JSON response (e.g., `xYz123`).

#### 3. Simulate a User Click (The Redirect)

This tests the core logic: Click recording, Redirecting, and Background Rewards.

```bash
curl -vL http://localhost:5000/link/YOUR_SHORT_CODE

```

* **Success Criteria:** * You see a `302 Found` status.
* The `Location` header points to the original Fiverr URL.
* Because of the `-L` flag, curl should eventually show the HTML of the Fiverr page.


#### 4. Verify Analytics and Rewards

Check if the click was counted and the reward was processed.

```bash
curl "http://localhost:5000/state?limit=1"

```

* **Success Criteria:** * `click_count` should be `1`.
* `credits_earned` should be `0.05`.


### Phase 3: Automated Testing Script

For a "Hiring Day" project, providing a test script is highly professional. Create a file named `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:5000"

def test_flow():
  # 1. Create Link
  payload = {"seller_id": "tester_1", "original_url": "https://fiverr.com/success"}
  res = requests.post(f"{BASE_URL}/link", json=payload)
  assert res.status_code in [200, 201]
  short_code = res.json()['link']['short_code']
  print(f"✅ Link Created: {short_code}")

  # 2. Trigger Click
  res = requests.get(f"{BASE_URL}/link/{short_code}", allow_redirects=False)
  assert res.status_code == 302
  print("✅ Redirect working")

  # 3. Verify State
  res = requests.get(f"{BASE_URL}/state")
  data = res.json()['data'][0]
  assert data['click_count'] >= 1
  print(f"✅ Analytics updated. Credits: {data['credits_earned']}")

if __name__ == "__main__":
  test_flow()

```

### Phase 4: Error Handling Scenarios

Run these to ensure your API doesn't crash on bad input:

| Scenario | Command | Expected Result |
| --- | --- | --- |
| **Missing Data** | `curl -X POST http://localhost:5000/link -d '{}'` | `400 Bad Request` |
| **Invalid Code** | `curl http://localhost:5000/link/doesnotexist` | `404 Not Found` |
| **Bad Pagination** | `curl http://localhost:5000/state?page=-1` | `400 Bad Request` |

### Testing Tip: The "Race Condition"

Your code uses `process_reward_async`. If you check the `/state` endpoint **immediately** (within milliseconds) after clicking, the `credits_earned` might still be `0.00` because the background thread hasn't finished. This is normal behavior for asynchronous systems!

