# Eco-Conscious Shopper 🌱

> Multi-agent AI system for real-time sustainability ratings of products and brands

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4)](https://ai.google.dev/)

## Overview

Eco-Conscious Shopper is an intelligent sustainability rating system that helps consumers make environmentally and ethically informed purchasing decisions. Using a multi-agent architecture powered by Google's Agent Development Kit (ADK) and Gemini AI, it analyzes products and brands across environmental impact, labor practices, and supply chain transparency.

### Key Features

- **Multi-Agent Collaboration**: Four specialized agents work together to research and analyze
- **Real-time Analysis**: Instant sustainability ratings (A-F grades) for products
- **Comprehensive Research**: Aggregates data from sustainability reports, ESG disclosures, supply chains, and news
- **Browser Extension**: Seamless integration while shopping online
- **Memory & Caching**: Efficient caching reduces redundant research
- **Production-Ready**: Deployable to Vertex AI Agent Engine

## 📚 Documentation

### Core Documentation
- **[Quick Start Guide](QUICKSTART.md)** ⚡ - Get running in 5 minutes
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** 🚀 - Complete build, run, and deploy instructions
- **[Documentation Maintenance](DOCUMENTATION_MAINTENANCE.md)** 📝 - Guide for maintaining docs

### Additional Resources
- **Installation Details** - See [Installation & Setup](#installation--setup) below
- **API Reference** - See [API Documentation](#api-documentation) below
- **Troubleshooting** - See [Common Issues](#troubleshooting) below

## Architecture

### Agent System

The system implements **four specialized agents** that collaborate to produce comprehensive sustainability ratings:

```
User Request → ResearchCoordinator (Orchestrator)
                      ↓
         ┌────────────┼────────────┐
         ↓            ↓            ↓
   WebResearch   SupplyChain   Sustainability
      Agent         Agent          Scorer
         ↓            ↓            ↓
         └────────────┼────────────┘
                      ↓
              Final Rating (A-F)
```

#### 1. ResearchCoordinator (Orchestrator)

**Responsibilities:**
- Parse product URLs and extract brand information
- Create and execute research plans with prioritized tasks
- Coordinate between specialized agents
- Maintain session state and research progress
- Validate and aggregate final results

**Key Concepts:** Planning, State Management, Orchestration

#### 2. WebResearchAgent (Tool Specialist)

**Responsibilities:**
- Search web for sustainability reports and ESG data
- Scrape company websites for environmental policies
- Gather recent news about labor practices
- Identify sustainability certifications

**Tools:**
- `search_sustainability_reports` - Find published ESG documents
- `scrape_company_esg_page` - Extract data from company websites
- `get_company_certifications` - Identify verified certifications
- `search_labor_practices_news` - Find recent news coverage
- `google_search` - General web search capability

**Key Concepts:** Tool Use (5+ tools), Web Scraping, API Integration

#### 3. SupplyChainAgent (Data Analyst)

**Responsibilities:**
- Analyze supply chain transparency using OpenSupplyHub API
- Calculate supply chain complexity metrics
- Assess geographic risk factors
- Provide transparency scoring
- Cache brand analyses for efficiency

**Tools:**
- `analyze_supply_chain` - Get comprehensive supply chain data
- `calculate_transparency_score` - Detailed transparency metrics

**Key Concepts:** Memory Implementation, Caching, API Integration

#### 4. SustainabilityScorer (Gemini-Powered)

**Responsibilities:**
- Synthesize research data from all sources
- Generate A-F ratings for environmental, labor, and transparency
- Provide detailed rationale for each rating
- Output structured JSON following Pydantic schemas
- Assess confidence in ratings

**Model:** `gemini-1.0-pro` (temperature: 0.1 for consistency)

**Key Concepts:** LLM Reasoning, Structured Output, Synthesis

## Project Structure

```
project/
├── agents/                          # Agent implementations
│   ├── research_coordinator.py      # Orchestrator with planning
│   ├── web_research_agent.py        # Tool specialist (5+ tools)
│   ├── supply_chain_agent.py        # With memory implementation
│   └── sustainability_scorer.py     # Gemini-powered scoring
├── models/                          # Pydantic data models
│   └── sustainability_models.py     # All schemas and models
├── tools/                           # Tool implementations
│   ├── web_scraper.py              # Playwright-based scraping
│   └── api_clients.py              # OpenSupplyHub, etc.
├── extension/                       # Chrome extension
│   ├── manifest.json
│   ├── popup/                      # Extension popup UI
│   ├── content/                    # Content scripts
│   └── background/                 # Background service worker
├── Dockerfile                       # For Vertex AI deployment
├── .agent_engine_config.json        # Deployment configuration
├── requirements.txt                 # Python dependencies
├── main.py                         # FastAPI application
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- Google Cloud Project with billing enabled
- Node.js (for extension development - optional)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Kaggle5dgai_EcoConscious_Shopper
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your configuration
nano .env
```

Required environment variables:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=1
```

### 4. Initialize Google Cloud

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

## Usage

### Running Locally

#### Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8080`

#### Test the API

```bash
# Health check
curl http://localhost:8080/health

# Analyze a product
curl -X POST http://localhost:8080/api/analyze-product \
  -H "Content-Type: application/json" \
  -d '{"product_url": "https://example.com/product/123"}'
```

### Installing the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/` directory
5. The extension icon should appear in your toolbar

### Using the Extension

1. Navigate to a product page on any e-commerce site
2. Click the Eco-Conscious Shopper extension icon
3. Click "Analyze This Page"
4. View the sustainability rating and detailed analysis

## Deployment to Vertex AI Agent Engine

### Prerequisites

1. Google Cloud Project with billing enabled
2. Vertex AI API enabled
3. Appropriate IAM permissions

### Deploy

```bash
# Build and deploy to Vertex AI Agent Engine
adk deploy agent_engine \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  . \
  --agent_engine_config_file=.agent_engine_config.json
```

### Monitor

```bash
# List deployed agents
gcloud ai reasoning-engines list \
  --project=YOUR_PROJECT_ID \
  --region=us-central1

# View logs
gcloud logging read \
  "resource.type=generic_task AND resource.labels.namespace=reasoning-engine" \
  --project=YOUR_PROJECT_ID \
  --limit=50
```

### Update Extension for Production

Update `extension/popup/popup.js`:

```javascript
const API_BASE_URL = "https://YOUR-AGENT-URL.vertex-ai.google.com";
```

## API Documentation

### Endpoints

#### `POST /api/analyze-product`

Analyze a product's sustainability.

**Request:**
```json
{
  "product_url": "https://example.com/product/123"
}
```

**Response:**
```json
{
  "rating": {
    "overall_score": "B",
    "environmental_score": "A",
    "labor_score": "B",
    "transparency_score": "C",
    "rationale": {
      "overall": "...",
      "environmental": "...",
      "labor": "...",
      "transparency": "..."
    },
    "confidence_score": 0.75,
    "research_timestamp": "2025-01-15T10:30:00Z",
    "brand": "Example Brand",
    "product_url": "https://example.com/product/123"
  },
  "processing_time_seconds": 12.5,
  "cached": false
}
```

#### `GET /api/cached-rating/{brand}`

Retrieve cached rating for a brand.

#### `GET /health`

Health check endpoint (required for Vertex AI).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "fastapi": true,
    "agents": true,
    "vertexai": true
  }
}
```

## Evaluation Criteria Alignment

This project meets all competition requirements:

### Category 1: The Pitch (30 points)

- **Core Concept (15 pts):** Clear problem/solution documented in README
- **Writeup (15 pts):** Comprehensive architecture documentation and diagrams

### Category 2: Implementation (70 points)

**Technical (50 pts):**
- ✅ **Multi-Agent Collaboration:** 4 specialized agents with clear roles
- ✅ **Tool Use:** 5+ tools across web scraping, APIs, and search
- ✅ **Planning:** ResearchCoordinator with state management
- ✅ **Memory:** SupplyChainAgent with caching implementation

**Documentation (20 pts):**
- ✅ Setup instructions
- ✅ Architecture diagrams
- ✅ API documentation
- ✅ Deployment guide

### Bonus Points (20 points)

- ✅ **Gemini Use (5 pts):** SustainabilityScorer powered by Gemini 1.0 Pro
- ✅ **Deployment (5 pts):** Configured for Vertex AI Agent Engine deployment
- **Video (10 pts):** [To be created]

## Data Models

The system uses Pydantic models for type safety and validation:

- `ResearchPlan` - Structured research plan with prioritized tasks
- `SustainabilityRating` - Final A-F rating with rationale
- `SupplyChainAnalysis` - Supply chain transparency assessment
- `ProductAnalysisRequest/Response` - API request/response schemas

See `models/sustainability_models.py` for complete schemas.

## Key Concepts Demonstrated

1. **Multi-Agent System:**
   - 4 specialized agents with clear responsibilities
   - Agent-to-agent communication via AgentTool
   - Orchestrator pattern with ResearchCoordinator

2. **Tool Use:**
   - Custom tools (5+ implemented)
   - Built-in tools (Google Search)
   - Web scraping with Playwright
   - API integration (OpenSupplyHub)

3. **Sessions & Memory:**
   - Session state management
   - Brand analysis caching
   - In-memory and disk-based memory

4. **Planning:**
   - Research plan creation
   - Task prioritization
   - State tracking (pending → researching → complete)

5. **Observability:**
   - Structured logging throughout
   - Health check endpoints
   - Processing time tracking

6. **Deployment:**
   - Dockerized application
   - Vertex AI Agent Engine configuration
   - Production-ready FastAPI server

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Structure

- **Agents** are independent modules with clear interfaces
- **Tools** are reusable functions wrapped with `FunctionTool`
- **Models** use Pydantic for validation
- **FastAPI** handles HTTP and CORS for browser extension

## Troubleshooting

### Common Issues

**Issue:** Playwright browser not found
```bash
# Solution: Install Playwright browsers
playwright install chromium
playwright install-deps
```

**Issue:** Google Cloud authentication failed
```bash
# Solution: Re-authenticate
gcloud auth application-default login
```

**Issue:** Extension can't connect to API
- Check API is running on `http://localhost:8080`
- Verify CORS is enabled in `main.py`
- Check browser console for errors

## Contributing

This is a competition entry project. After competition, contributions may be welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Copyright 2025

Licensed under the Apache License, Version 2.0. See LICENSE file for details.

## Development Tools & AI Assistance Disclosure

**AI-Assisted Development**: This project was developed with assistance from AI coding tools, including Anthropic's Claude, which were used as development aids for code generation, debugging, documentation, and architectural planning. The use of AI assistants complies with the [Kaggle Competition Rules](https://www.kaggle.com/competitions/agents-intensive-capstone-project/rules), specifically:

- **Section 6 (External Data and Tools)**: AI assistants like Claude are publicly available tools accessible to all participants
- **Section 6.c (AMLT)**: Automated tools may be used to create submissions
- **Reasonableness Criteria**: Claude's free tier is publicly accessible; the Pro tier ($20/month) constitutes minimal cost well below competition prize values

**Original Work**: All code, architecture, and implementation decisions represent original work by the competition participant(s). AI tools were used as assistants in the development process, similar to using documentation, Stack Overflow, or other development resources.

**Open Source Compliance**: All code in this repository, including any AI-assisted portions, is released under the CC-BY-SA 4.0 license as required by the competition rules for winning submissions. The code is provided with full documentation and reproduction instructions as specified in Section 8 (Winner's Obligations).

**Transparency**: This disclosure is provided in the spirit of transparency and good sportsmanship within the Kaggle community, following practices documented in the community (see: [How to use ChatGPT in a competition](https://www.kaggle.com/code/jacoporepossi/how-to-use-chatgpt-in-a-competition-eda-part-1) and [community discussions](https://www.kaggle.com/questions-and-answers/407349)).

## Acknowledgments

- Built with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- Powered by [Google Gemini](https://ai.google.dev/gemini-api)
- Deployed on [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- Supply chain data from [OpenSupplyHub](https://opensupplyhub.org/)
- Kaggle 5-Day AI Agents Course

## Contact

For questions or issues, please open an issue on GitHub.

---

**Built for the Kaggle 5-Day AI Agents Capstone Competition**