# 🚀 QUICK START - RUN THIS PROJECT IN 2 MINUTES

## Option 1: Fastest (Docker) - RECOMMENDED
```bash
# 1. Build and run with minimal setup
docker-compose -f docker-compose.minimal.yml up --build

# 2. Open browser
# Frontend: http://localhost:3000
# API: http://localhost:8001/docs

# 3. Test the API (optional)
python test_api.py
```

## Option 2: Local Development (No Docker)
```bash
# 1. Run the automated script
./run_local.sh

# 2. Open browser to http://localhost:3000
```

## Option 3: Manual Setup

### Backend Only (Minimal)
```bash
# 1. Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-minimal.txt

# 3. Run backend
python -m uvicorn src.api.main_simple:app --port 8001

# 4. Test API
curl http://localhost:8001/health
python test_api.py
```

### Frontend (After Backend is Running)
```bash
# 1. Install dependencies
cd frontend
npm install --legacy-peer-deps

# 2. Start frontend
REACT_APP_API_URL=http://localhost:8001 npm start

# 3. Open http://localhost:3000
```

## 🧪 Test Everything Works

Run the test suite:
```bash
python test_api.py
```

You should see:
```
✅ ALL TESTS PASSED SUCCESSFULLY!
```

## 📱 What You Can Do

Once running, you can:

1. **Upload Documents** - Go to Documents page, click Upload
2. **Run Compliance Analysis** - Go to Compliance page, select GDPR, click Start
3. **View Risk Dashboard** - Check the main Dashboard for metrics
4. **Generate Reports** - Go to Reports page to create executive summaries
5. **Monitor Agents** - See the 5 AI agents working in the Compliance section

## ⚠️ Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8001
lsof -i :8001
kill -9 <PID>

# Find and kill process on port 3000
lsof -i :3000
kill -9 <PID>
```

### Docker Issues
```bash
# Complete cleanup and rebuild
docker-compose -f docker-compose.minimal.yml down -v
docker system prune -a
docker-compose -f docker-compose.minimal.yml up --build
```

### NPM Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install --legacy-peer-deps
```

### Python Issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
```

## ✅ Success Checklist

- [ ] Backend responds at http://localhost:8001/health
- [ ] Frontend loads at http://localhost:3000
- [ ] Dashboard shows compliance metrics
- [ ] Can navigate between pages
- [ ] API test script passes
- [ ] No errors in console

## 📞 Need Help?

1. Check `TEST_WORKFLOW.md` for detailed testing steps
2. Review `QUICKSTART.md` for more options
3. See full `README.md` for complete documentation

---
**Note**: This is a simplified version for testing. The full version includes PostgreSQL, Redis, and ChromaDB for production use.