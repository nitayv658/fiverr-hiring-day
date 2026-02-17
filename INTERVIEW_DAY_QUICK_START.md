# 🚀 INTERVIEW DAY — QUICK START (February 17, 2026)

## ⏰ Morning Setup (5 minutes)

### 1. Start PostgreSQL (Already Running ✅)
```bash
# PostgreSQL is already running as a service
# Verify it's up:
brew services list | grep postgresql

# If needed, restart:
brew services restart postgresql@15
```

### 2. Start Flask API
```bash
cd /Users/nitay658/Documents/Projects/Fiverr-project
source venv/bin/activate
python app.py
```

### 3. Test It Works
```bash
# In a new terminal:
curl http://localhost:5000/health
curl http://localhost:5000/
```

---

## 🔑 AWS Setup — ALREADY CONFIGURED ✅

### Load Bedrock Credentials:
```bash
source aws_credentials.sh

# Or manually:
export AWS_BEARER_TOKEN_BEDROCK="bedrock-api-key-..."
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=eu-west-1
```

### Verify it's set:
```bash
echo $AWS_BEARER_TOKEN_BEDROCK
echo $AWS_REGION
```

### In VS Code:
1. Click Spark icon (✱) in bottom-right
2. Type something to test Claude
3. If working → you're good!
4. If not → check env vars above

---

## 📊 Database is Ready

**Connection Details:**
- Host: `localhost`
- Port: `5432`
- Database: `fiverr_test`
- Username: `user`
- Password: `password`

**Test connection:**
```bash
/opt/homebrew/opt/postgresql@15/bin/psql -U user -d fiverr_test -c "SELECT NOW();"
```

---

## 📝 Quick Commands

**Flask API:**
- Default: `http://localhost:5000`
- Health check: `curl http://localhost:5000/health`
- Create test message: `curl -X POST http://localhost:5000/messages -H "Content-Type: application/json" -d '{"text": "Test"}'`

**Database:**
- Connect: `/opt/homebrew/opt/postgresql@15/bin/psql -U user -d fiverr_test`
- List tables: `\dt`
- Exit: `\q`

**Git:**
- Check status: `git status`
- Commit: `git add -A && git commit -m "message"`
- Push: `git push origin main`

---

## 📚 Resources

- **Full Handbook:** `fiverr_interview_day_handbook.md` (open in VS Code, Ctrl+F to search)
- **AWS Setup:** `AWS_SETUP.md`
- **GitHub Repo:** https://github.com/nitayv658/fiverr-hiring-day
- **This File:** Keep open in a browser tab or VS Code

---

## ✅ Checklist for Tomorrow

- [ ] Laptop fully charged + charger in bag
- [ ] Arrive by 9:00 AM
- [ ] Start PostgreSQL (already set up ✅)
- [ ] Open project in VS Code
- [ ] Start Flask API: `python app.py`
- [ ] Test health endpoint with curl
- [ ] Fill in AWS credentials when provided
- [ ] Open interview handbook (Ctrl+F to search)
- [ ] Good luck! 🎯

---

**Your setup is complete. You're ready!** 🚀
