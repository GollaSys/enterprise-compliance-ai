# Quick Start Guide

## 🚀 Fastest Setup (Development)

### Option 1: Docker (Recommended)
```bash
# Test and start Docker setup
./docker-test.sh

# OR manually:
docker-compose build
docker-compose up -d

# Verify it's working:
curl http://localhost:8001/health

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8001
# - API Docs: http://localhost:8001/docs
```

### Option 2: Manual Setup

#### 1. Start Dependencies Only
```bash
# Start only the databases
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here (optional)

# Run backend
uvicorn src.api.main:app --reload --port 8001
```

#### 3. Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Start frontend
npm start
```

## 🔑 Required API Keys

Edit `.env` file and add:
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional
```

## 📱 Access Points

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **ChromaDB**: localhost:8000

## 🧪 Test the Setup

1. Navigate to http://localhost:3000
2. Go to Documents page and upload a test document
3. Navigate to Compliance page and run an analysis
4. Check the Dashboard for metrics

## 🛑 Troubleshooting

### Docker Issues
```bash
# Clean restart
docker-compose down -v
docker-compose up --build
```

### NPM Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Python Issues
```bash
poetry env remove python
poetry install
```

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # or :3000, :8001, etc.

# Kill the process
kill -9 <PID>
```

## 📚 Next Steps

1. Upload regulatory documents in the Documents section
2. Configure policies in the Policies section
3. Run compliance analysis
4. Review risk assessments
5. Generate executive reports