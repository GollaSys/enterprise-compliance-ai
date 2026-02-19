# Complete Test Workflow Guide

## 🧪 Testing the Compliance AI Platform

### 1. Quick Start with Docker (Simplest)

```bash
# Use the minimal docker compose for quick testing
docker-compose -f docker-compose.minimal.yml up --build

# Wait for services to start (about 30 seconds)
# Then test the API
python test_api.py
```

### 2. Local Development Setup

```bash
# Run the automated setup script
./run_local.sh

# In another terminal, run tests
python test_api.py
```

### 3. Manual Testing Steps

#### Step 1: Start Backend Only
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies
pip install -r requirements-minimal.txt

# Run the simplified backend
python -m uvicorn src.api.main_simple:app --port 8001 --reload
```

#### Step 2: Test Backend API
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test dashboard metrics
curl http://localhost:8001/api/v1/dashboard/metrics

# Run full test suite
python test_api.py
```

#### Step 3: Start Frontend
```bash
cd frontend
npm install --legacy-peer-deps
REACT_APP_API_URL=http://localhost:8001 npm start
```

### 4. Complete Use Case Testing

#### Use Case 1: Document Upload and Processing
1. Open browser to http://localhost:3000
2. Navigate to Documents page
3. Click "Upload Document"
4. Select any PDF or text file
5. Verify document appears in the list

#### Use Case 2: Compliance Analysis
1. Navigate to Compliance page
2. Select "GDPR" from regulation dropdown
3. Click "Start Analysis"
4. Wait for analysis to complete
5. Review compliance score and gaps

#### Use Case 3: Risk Assessment
1. Navigate to Risks page
2. Review risk distribution
3. Check mitigation progress
4. Verify risk scores are displayed

#### Use Case 4: Report Generation
1. Navigate to Reports page
2. Click on any "Generate" button
3. Select report type and period
4. Download generated report

#### Use Case 5: Dashboard Monitoring
1. Navigate to Dashboard
2. Verify all metrics load
3. Check compliance trend chart
4. Review recent activities

### 5. API Endpoint Testing

Run the automated test suite:
```bash
python test_api.py
```

Expected output:
```
==================================================
COMPLIANCE AI PLATFORM - API TEST SUITE
==================================================
Testing health endpoint...
✅ Health check: {'status': 'healthy'}

Testing dashboard endpoints...
✅ Dashboard metrics - Compliance: 92%
✅ Recent activities: 2 items

Testing compliance endpoints...
✅ Available regulations: 3
✅ Compliance analysis - Score: 92.5%
   - Gaps found: 2
   - Risks identified: 2

Testing document endpoints...
✅ Documents in system: 0
✅ Document uploaded: DOC-20240101120000

Testing agent endpoints...
✅ Agent system status: operational
   - Regulatory Analyst: active (42 tasks)
   - Policy Mapper: active (38 tasks)
   - Evidence Validator: active (56 tasks)
   - Risk Scorer: active (29 tasks)
   - Executive Reporter: active (15 tasks)

Testing report endpoints...
✅ Report generated: RPT-20240101120000
✅ Total reports: 1

==================================================
✅ ALL TESTS PASSED SUCCESSFULLY!
==================================================
```

### 6. Troubleshooting Common Issues

#### Backend won't start
```bash
# Check port 8001 is free
lsof -i :8001
# Kill any process using it
kill -9 <PID>

# Verify Python installation
python3 --version  # Should be 3.11+

# Reinstall dependencies
pip install --force-reinstall -r requirements-minimal.txt
```

#### Frontend won't start
```bash
# Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm start
```

#### Docker build fails
```bash
# Clean Docker cache
docker system prune -a
docker-compose -f docker-compose.minimal.yml build --no-cache
```

### 7. Performance Testing

```python
# Run concurrent requests test
import concurrent.futures
import requests
import time

def test_concurrent():
    url = "http://localhost:8001/api/v1/dashboard/metrics"

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(requests.get, url) for _ in range(100)]
        results = [f.result() for f in futures]

    elapsed = time.time() - start
    success = sum(1 for r in results if r.status_code == 200)

    print(f"Processed {success}/100 requests in {elapsed:.2f}s")
    print(f"Requests per second: {100/elapsed:.2f}")

test_concurrent()
```

### 8. Integration Testing

```bash
# Test full workflow via API
curl -X POST http://localhost:8001/api/v1/documents/upload \
  -F "file=@test.pdf"

curl -X POST http://localhost:8001/api/v1/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{"regulation_type": "GDPR", "document_ids": ["DOC-001"]}'

curl http://localhost:8001/api/v1/reports/generate?report_type=executive&period=Q4
```

### 9. Browser Testing

1. **Chrome DevTools Network Tab**
   - Open Chrome DevTools (F12)
   - Go to Network tab
   - Navigate through the app
   - Verify all API calls return 200 status

2. **React Developer Tools**
   - Install React DevTools extension
   - Inspect component state
   - Verify data flow

### 10. Production Readiness Checklist

- [ ] All API endpoints return correct data
- [ ] Frontend loads without errors
- [ ] Document upload works
- [ ] Compliance analysis runs
- [ ] Reports generate successfully
- [ ] Dashboard metrics display
- [ ] No console errors in browser
- [ ] API responds within 500ms
- [ ] Docker containers stay healthy
- [ ] Memory usage stays under 1GB

## ✅ Success Criteria

The platform is working correctly when:

1. Backend API starts on port 8001
2. Frontend starts on port 3000
3. All API tests pass (run `python test_api.py`)
4. UI navigation works without errors
5. Data persists between page refreshes
6. Charts and visualizations render properly
7. File upload accepts documents
8. Compliance analysis returns results
9. Reports can be generated
10. No critical errors in console or logs