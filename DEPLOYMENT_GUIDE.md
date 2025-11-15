# Deployment Guide - Eco-Conscious Shopper

> Complete guide for building, starting, and deploying the Eco-Conscious Shopper application

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Building the Application](#building-the-application)
4. [Running Locally](#running-locally)
5. [Deploying to Vertex AI Agent Engine](#deploying-to-vertex-ai-agent-engine)
6. [Deploying the Chrome Extension](#deploying-the-chrome-extension)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Cleanup & Teardown](#cleanup--teardown)

---

## Prerequisites

### Required Tools

- **Python 3.11+**
  - Check version: `python --version`
  - Download: https://www.python.org/downloads/

- **Google Cloud SDK**
  - Check version: `gcloud --version`
  - Download: https://cloud.google.com/sdk/docs/install

- **Git**
  - Check version: `git --version`
  - Download: https://git-scm.com/downloads

- **Docker** (optional, for local containerized testing)
  - Check version: `docker --version`
  - Download: https://docs.docker.com/get-docker/

### Google Cloud Setup

#### 1. Create/Select Google Cloud Project

```bash
# Create a new project
gcloud projects create eco-conscious-shopper --name="Eco-Conscious Shopper"

# Or list existing projects
gcloud projects list

# Set active project
gcloud config set project YOUR_PROJECT_ID
```

#### 2. Enable Billing

1. Navigate to: https://console.cloud.google.com/billing
2. Link a billing account to your project
3. Verify billing is enabled:
   ```bash
   gcloud billing accounts list
   ```

#### 3. Enable Required APIs

```bash
# Enable all required APIs in one command
gcloud services enable \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com
```

Verify APIs are enabled:
```bash
gcloud services list --enabled
```

#### 4. Set Up Authentication

```bash
# Authenticate with your Google account
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Verify authentication
gcloud auth list
```

#### 5. Create Service Account (Optional but Recommended)

```bash
# Create service account
gcloud iam service-accounts create eco-shopper-sa \
    --display-name="Eco-Conscious Shopper Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:eco-shopper-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:eco-shopper-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create ~/eco-shopper-key.json \
    --iam-account=eco-shopper-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/eco-shopper-key.json
```

---

## Local Development Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd Kaggle5dgai_EcoConscious_Shopper

# Verify you're in the correct directory
ls -la
# Should see: agents/, models/, tools/, extension/, main.py, etc.
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show venv in prompt)
which python  # macOS/Linux
where python  # Windows
```

### 3. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep google-adk
pip list | grep fastapi
```

### 4. Install Playwright Browsers

```bash
# Install Chromium browser for Playwright
playwright install chromium

# Install system dependencies
playwright install-deps chromium

# Verify installation
playwright --version
```

### 5. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Edit `.env` with your configuration:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id-here
GOOGLE_CLOUD_LOCATION=global

# Set to 1 to use Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=1

# API Configuration
PORT=8080

# Application Settings
CACHE_DIR=./cache
LOG_LEVEL=INFO
```

**Important:** Replace `your-project-id-here` with your actual Google Cloud Project ID.

### 6. Verify Setup

```bash
# Check Python packages
python -c "import google.adk; print('ADK installed')"
python -c "import fastapi; print('FastAPI installed')"
python -c "import playwright; print('Playwright installed')"

# Check environment variables
python -c "import os; print(os.getenv('GOOGLE_CLOUD_PROJECT'))"
```

---

## Building the Application

### 1. Project Structure Verification

```bash
# Verify all required directories exist
ls -la agents/
ls -la models/
ls -la tools/
ls -la extension/

# Verify key files exist
ls -la main.py
ls -la requirements.txt
ls -la Dockerfile
ls -la .agent_engine_config.json
```

### 2. Create Cache Directory

```bash
# Create cache directory for brand analyses
mkdir -p cache

# Set permissions (macOS/Linux)
chmod 755 cache
```

### 3. Validate Code (Optional)

```bash
# Run Python syntax check on all files
python -m py_compile agents/*.py
python -m py_compile models/*.py
python -m py_compile tools/*.py
python -m py_compile main.py

# Or use flake8 for linting (if installed)
pip install flake8
flake8 --max-line-length=100 .
```

### 4. Build Docker Image (Optional - for local testing)

```bash
# Build Docker image
docker build -t eco-conscious-shopper:latest .

# Verify image was built
docker images | grep eco-conscious-shopper

# Test run the image
docker run -p 8080:8080 \
    -e GOOGLE_CLOUD_PROJECT=your-project-id \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -v ~/.config/gcloud:/app/.config/gcloud \
    eco-conscious-shopper:latest
```

---

## Running Locally

### Method 1: Direct Python Execution (Recommended for Development)

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run the application
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Method 2: Using Uvicorn Directly

```bash
# Run with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Or with more workers for production-like testing
uvicorn main:app --workers 2 --host 0.0.0.0 --port 8080
```

### Method 3: Using Docker

```bash
# Run the Docker container
docker run -d \
    --name eco-shopper \
    -p 8080:8080 \
    -e GOOGLE_CLOUD_PROJECT=your-project-id \
    -v $(pwd)/cache:/app/cache \
    eco-conscious-shopper:latest

# View logs
docker logs -f eco-shopper

# Stop container
docker stop eco-shopper
docker rm eco-shopper
```

### Testing the Local Server

#### 1. Health Check

```bash
# Using curl
curl http://localhost:8080/health

# Using httpie (if installed)
http http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-15T10:30:00Z",
#   "services": {
#     "fastapi": true,
#     "agents": true,
#     "vertexai": true
#   }
# }
```

#### 2. Test Product Analysis

```bash
# Analyze a product
curl -X POST http://localhost:8080/api/analyze-product \
    -H "Content-Type: application/json" \
    -d '{"product_url": "https://example.com/product/123"}'

# Pretty print response with jq (if installed)
curl -X POST http://localhost:8080/api/analyze-product \
    -H "Content-Type: application/json" \
    -d '{"product_url": "https://example.com/product/123"}' | jq
```

#### 3. Test Cache Endpoint

```bash
# Check cached rating
curl http://localhost:8080/api/cached-rating/Example

# Get API stats
curl http://localhost:8080/api/stats
```

#### 4. Access API Documentation

Open in browser:
- Main API: http://localhost:8080
- API Docs (Swagger): http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## Deploying to Vertex AI Agent Engine

### Pre-Deployment Checklist

- [ ] Google Cloud Project created and billing enabled
- [ ] All required APIs enabled
- [ ] Authentication configured
- [ ] Application tested locally
- [ ] Environment variables configured
- [ ] No API keys hardcoded in code

### Deployment Steps

#### 1. Verify ADK Installation

```bash
# Check ADK is installed
adk --version

# If not installed
pip install google-adk
```

#### 2. Set Deployment Region

```bash
# Choose a region close to your users
# Available regions: us-central1, us-east4, us-west1, europe-west1, europe-west4

export DEPLOY_REGION=us-central1
```

#### 3. Review Deployment Configuration

Check `.agent_engine_config.json`:

```json
{
  "min_instances": 0,      # Scale to zero when idle (saves cost)
  "max_instances": 5,      # Maximum concurrent instances
  "resource_limits": {
    "cpu": "2",           # 2 CPU cores per instance
    "memory": "4Gi"       # 4GB RAM per instance
  },
  "scaling": {
    "cpu_utilization_target": 70,  # Scale up at 70% CPU
    "min_request_count": 1
  },
  "timeout": "300s"       # 5 minute timeout per request
}
```

Adjust these values based on your needs:
- **Development/Testing**: Keep `min_instances: 0` and `max_instances: 2`
- **Production Low Traffic**: `min_instances: 1`, `max_instances: 5`
- **Production High Traffic**: `min_instances: 3`, `max_instances: 20`

#### 4. Deploy to Agent Engine

```bash
# Navigate to project directory
cd Kaggle5dgai_EcoConscious_Shopper

# Deploy
adk deploy agent_engine \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$DEPLOY_REGION \
    . \
    --agent_engine_config_file=.agent_engine_config.json
```

**Expected Output:**
```
Deploying agent to Agent Engine...
✅ Packaging agent code
✅ Uploading to Cloud Storage
✅ Building container image
✅ Deploying container
✅ Agent deployed successfully

Resource name: projects/123456789/locations/us-central1/reasoningEngines/abc123def456
Endpoint URL: https://us-central1-aiplatform.googleapis.com/v1/projects/123456789/locations/us-central1/reasoningEngines/abc123def456
```

**Deployment Time:** Typically 3-7 minutes

#### 5. Verify Deployment

```bash
# List deployed agents
gcloud ai reasoning-engines list \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$DEPLOY_REGION

# Get specific agent details
gcloud ai reasoning-engines describe AGENT_ID \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$DEPLOY_REGION
```

#### 6. Test Deployed Agent

```bash
# Using Python SDK
python << EOF
import vertexai
from vertexai import agent_engines

vertexai.init(project="YOUR_PROJECT_ID", location="$DEPLOY_REGION")

agents = list(agent_engines.list())
if agents:
    agent = agents[0]
    print(f"Testing agent: {agent.resource_name}")

    # Test query
    response = agent.query(
        message="Analyze https://example.com/product",
        user_id="test_user"
    )
    print(response)
EOF
```

### Alternative Deployment: Cloud Run (Optional)

If you prefer Cloud Run instead of Agent Engine:

```bash
# Build and push container
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/eco-shopper

# Deploy to Cloud Run
gcloud run deploy eco-conscious-shopper \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT/eco-shopper \
    --platform managed \
    --region $DEPLOY_REGION \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=global

# Get service URL
gcloud run services describe eco-conscious-shopper \
    --platform managed \
    --region $DEPLOY_REGION \
    --format 'value(status.url)'
```

---

## Deploying the Chrome Extension

### For Development (Local Testing)

#### 1. Configure Extension for Local API

Edit `extension/popup/popup.js`:

```javascript
// For local testing
const API_BASE_URL = "http://localhost:8080";
```

#### 2. Load Extension in Chrome

1. Open Chrome
2. Navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top-right)
4. Click **Load unpacked**
5. Select the `extension/` directory
6. Extension icon appears in toolbar

#### 3. Test Extension

1. Navigate to any e-commerce product page
2. Click the extension icon
3. Click "Analyze This Page"
4. Verify it connects to your local API

### For Production (Deployed API)

#### 1. Update API Endpoint

Edit `extension/popup/popup.js`:

```javascript
// For production - use your deployed Agent Engine URL
const API_BASE_URL = "https://YOUR-AGENT-URL.vertex-ai.google.com";

// Or Cloud Run URL
const API_BASE_URL = "https://eco-conscious-shopper-xxx-uc.a.run.app";
```

#### 2. Update Extension Permissions

Edit `extension/manifest.json`:

```json
{
  "host_permissions": [
    "https://*.vertex-ai.google.com/*",
    "https://*.run.app/*"
  ]
}
```

#### 3. Create Production Build

```bash
# Navigate to extension directory
cd extension

# Create a zip file for distribution
zip -r eco-conscious-shopper-extension.zip . \
    -x "*.DS_Store" \
    -x "*/.git/*" \
    -x "*/node_modules/*"

# Verify zip contents
unzip -l eco-conscious-shopper-extension.zip
```

#### 4. Publish to Chrome Web Store (Optional)

1. Create Chrome Web Store developer account: https://chrome.google.com/webstore/devconsole
2. Pay one-time $5 developer fee
3. Click **New Item**
4. Upload `eco-conscious-shopper-extension.zip`
5. Fill in store listing details:
   - Name: Eco-Conscious Shopper
   - Description: Get instant sustainability ratings...
   - Screenshots (1280x800 or 640x400)
   - Icon (128x128)
6. Submit for review

**Review time:** Typically 1-3 days

---

## Monitoring & Troubleshooting

### Viewing Logs

#### Agent Engine Logs

```bash
# View recent logs
gcloud logging read \
    "resource.type=generic_task AND resource.labels.namespace=reasoning-engine" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --limit=50 \
    --format=json

# Stream logs in real-time
gcloud logging read \
    "resource.type=generic_task AND resource.labels.namespace=reasoning-engine" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --limit=50 \
    --format=json \
    --freshness=1m
```

#### Cloud Run Logs (if using Cloud Run)

```bash
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=eco-conscious-shopper" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --limit=50
```

### Monitoring Performance

#### Via Cloud Console

1. Navigate to: https://console.cloud.google.com/monitoring
2. Select your project
3. Create dashboard for:
   - Request count
   - Latency (p50, p95, p99)
   - Error rate
   - CPU/Memory utilization

#### Via gcloud

```bash
# Get metrics
gcloud monitoring time-series list \
    --filter='metric.type="run.googleapis.com/request_count"' \
    --project=$GOOGLE_CLOUD_PROJECT
```

### Common Issues & Solutions

#### Issue 1: Deployment Fails - "APIs not enabled"

**Solution:**
```bash
# Re-enable all required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com

# Wait 2 minutes, then retry deployment
```

#### Issue 2: "Permission Denied" Errors

**Solution:**
```bash
# Check current permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Add required role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="user:YOUR_EMAIL@gmail.com" \
    --role="roles/aiplatform.user"
```

#### Issue 3: Extension Can't Connect to API

**Troubleshooting:**
1. Check API URL in `extension/popup/popup.js`
2. Verify CORS is enabled in `main.py`
3. Check browser console for errors (F12)
4. Test API endpoint directly:
   ```bash
   curl https://your-api-url.com/health
   ```

#### Issue 4: Slow Response Times

**Solutions:**
- Increase `max_instances` in `.agent_engine_config.json`
- Increase `resource_limits.cpu` and `memory`
- Enable caching more aggressively
- Add CDN for static assets

#### Issue 5: High Costs

**Solutions:**
- Set `min_instances: 0` for scale-to-zero
- Reduce `max_instances`
- Use cheaper model (already using flash-lite)
- Implement request rate limiting
- Set up billing alerts

### Setting Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s
```

---

## Cleanup & Teardown

### Delete Deployed Agent

```bash
# List agents to get ID
gcloud ai reasoning-engines list \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$DEPLOY_REGION

# Delete specific agent
gcloud ai reasoning-engines delete AGENT_ID \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$DEPLOY_REGION \
    --quiet

# Or delete via Python
python << EOF
import vertexai
from vertexai import agent_engines

vertexai.init(project="$GOOGLE_CLOUD_PROJECT", location="$DEPLOY_REGION")

agents = list(agent_engines.list())
for agent in agents:
    print(f"Deleting {agent.resource_name}")
    agent_engines.delete(resource_name=agent.resource_name, force=True)
EOF
```

### Delete Cloud Run Service (if used)

```bash
gcloud run services delete eco-conscious-shopper \
    --region=$DEPLOY_REGION \
    --quiet
```

### Clean Up Local Resources

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove cache
rm -rf cache/

# Remove Docker images (if created)
docker rmi eco-conscious-shopper:latest

# Remove downloaded credentials
rm ~/eco-shopper-key.json
```

### Delete Google Cloud Project (Complete Cleanup)

**⚠️ Warning: This deletes EVERYTHING in the project!**

```bash
# List all resources first
gcloud projects describe $GOOGLE_CLOUD_PROJECT

# Delete project
gcloud projects delete $GOOGLE_CLOUD_PROJECT

# Confirm deletion
gcloud projects list | grep $GOOGLE_CLOUD_PROJECT
```

---

## Quick Reference Commands

### Development
```bash
source venv/bin/activate          # Activate environment
python main.py                     # Start server
curl http://localhost:8080/health  # Test health
```

### Deployment
```bash
adk deploy agent_engine --project=$PROJECT_ID --region=$REGION . --agent_engine_config_file=.agent_engine_config.json
```

### Monitoring
```bash
gcloud ai reasoning-engines list --project=$PROJECT_ID --region=$REGION
gcloud logging read "resource.type=generic_task" --limit=50
```

### Cleanup
```bash
gcloud ai reasoning-engines delete AGENT_ID --project=$PROJECT_ID --region=$REGION
```

---

## Support & Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **Vertex AI Agent Engine**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- **Troubleshooting FAQ**: See README.md
- **Issues**: Open an issue on GitHub

---

**Last Updated:** 2025-01-15
