# Quick Start Guide

> Get up and running with Eco-Conscious Shopper in 5 minutes

## Prerequisites

- Python 3.11+
- Google Cloud Project
- Git

## 1. Clone & Setup (2 minutes)

```bash
# Clone repository
git clone <repository-url>
cd Kaggle5dgai_EcoConscious_Shopper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

## 2. Configure Environment (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google Cloud Project ID
nano .env  # or use any editor
```

**Required in `.env`:**
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=1
```

## 3. Authenticate with Google Cloud (1 minute)

```bash
# Login and set up credentials
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com storage.googleapis.com
```

## 4. Run Application (1 minute)

```bash
# Start the server
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## 5. Test It Works

```bash
# In a new terminal, test the API
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","timestamp":"...","services":{...}}
```

## 6. Use Chrome Extension (Optional)

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `extension/` folder
5. Navigate to any product page and click the extension icon

---

## Next Steps

- **Full Documentation**: See [README.md](README.md)
- **Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **API Testing**: Visit http://localhost:8080/docs for Swagger UI

## Common Issues

**Issue:** `ModuleNotFoundError: No module named 'google.adk'`
```bash
# Solution: Install requirements
pip install -r requirements.txt
```

**Issue:** `Playwright browser not found`
```bash
# Solution: Install browser
playwright install chromium
playwright install-deps
```

**Issue:** `Permission denied` errors
```bash
# Solution: Re-authenticate
gcloud auth application-default login
```

---

## Quick Command Reference

```bash
# Start server
python main.py

# Test health endpoint
curl http://localhost:8080/health

# Analyze a product
curl -X POST http://localhost:8080/api/analyze-product \
  -H "Content-Type: application/json" \
  -d '{"product_url": "https://example.com/product"}'

# Deploy to Vertex AI
adk deploy agent_engine --project=$GOOGLE_CLOUD_PROJECT --region=us-central1 .
```

---

**Last Updated:** 2025-01-15
