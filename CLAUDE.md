# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the web research application
python run_app.py
# Access at http://localhost:8000
```

### Running Tests
```bash
# Test web connectivity with SSL handling
python test_web_connectivity.py

# Test complete LLM integration (OAuth + Cohere)
python test_cohere_complete.py
```

## Architecture Overview

This is a web research framework that combines web scraping capabilities with LLM integration using Cohere models via OpenAI-compatible API. The framework handles enterprise SSL certificates and OAuth authentication.

### Core Components

1. **SSL Certificate Handling**
   - Certificates stored in `ssl_certs/` folder
   - Dual strategy: requests first with urllib3 fallback for SSL issues
   - Special handling for known problematic sites (GitHub)

2. **OAuth Authentication Flow**
   - Client credentials flow to obtain access tokens
   - Configurable retry logic with exponential backoff
   - Token used as API key for OpenAI client

3. **LLM Integration**
   - Uses OpenAI client library with custom base URL
   - Supports Cohere models: `gpt-4o-mini-2024-07-18` and `gpt-4o-2024-05-13`
   - Streaming and tool calling capabilities

### Configuration Requirements

Before running the application, update `config.py`:
- `OAUTH_URL`: OAuth token endpoint
- `OAUTH_CLIENT_ID`: OAuth client ID
- `OAUTH_CLIENT_SECRET`: OAuth client secret  
- `BASE_URL`: API base URL for OpenAI-compatible endpoint

SSL certificate (`rbc-ca-bundle.cer`) must be placed in `ssl_certs/` folder.

## File Structure

```
web_research/
├── ssl_certs/
│   ├── README.md
│   └── rbc-ca-bundle.cer          # Your SSL certificate
├── static/
│   └── index.html                 # Web UI
├── agent.py                       # Research agent with tool calling
├── app.py                         # FastAPI web application  
├── run_app.py                     # Application launcher
├── config.py                      # Configuration settings
├── test_web_connectivity.py       # Web access test
├── test_cohere_complete.py        # Complete LLM integration test
├── requirements.txt               # Dependencies
├── CLAUDE.md                      # This file
└── README.md                      # Project documentation
```