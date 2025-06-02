# Web Research Framework

A comprehensive framework for AI-powered web research and report generation using enterprise-grade authentication and SSL handling.

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure SSL Certificate
```bash
# Copy your SSL certificate to the ssl_certs folder
cp /path/to/your/rbc-ca-bundle.cer ssl_certs/
```

### 3. Configure API Endpoints
Edit the `CONFIG` section in `test_cohere_complete.py`:
```python
CONFIG = {
    # OAuth Configuration - UPDATE THESE
    "OAUTH_URL": "https://your-oauth-endpoint.com/oauth/token",
    "OAUTH_CLIENT_ID": "your-client-id", 
    "OAUTH_CLIENT_SECRET": "your-client-secret",
    
    # API Configuration - UPDATE THIS  
    "BASE_URL": "https://your-api-endpoint.com/v1",
}
```

### 4. Test Components

#### Test Web Connectivity
```bash
python test_web_connectivity.py
```
Tests external website access with smart SSL handling for enterprise environments.

#### Test Cohere Model Integration
```bash
python test_cohere_complete.py
```
Tests complete authentication flow and LLM capabilities:
- SSL certificate setup
- OAuth authentication
- OpenAI client with Cohere models
- Streaming responses
- Tool calling functionality

## Architecture

### Core Components Tested

1. **Web Connectivity** (`test_web_connectivity.py`)
   - Smart SSL handling (requests + urllib3 fallback)
   - Enterprise certificate chain compatibility  
   - External website access validation

2. **LLM Integration** (`test_cohere_complete.py`)
   - SSL certificate configuration
   - OAuth client credentials flow
   - OpenAI client with custom base URL
   - Streaming and tool calling capabilities

### SSL Strategy
- **Normal sites**: requests first, urllib3 fallback on SSL errors
- **Known problematic sites** (GitHub): urllib3 first, requests fallback
- **Enterprise certificates**: Automatic detection from `ssl_certs/` folder

### Authentication Flow
1. Load SSL certificate from `ssl_certs/rbc-ca-bundle.cer`
2. OAuth client credentials flow to get access token
3. Configure OpenAI client with base URL and OAuth token
4. Test API capabilities (basic, streaming, tools)

## File Structure
```
web_research/
├── ssl_certs/
│   ├── README.md
│   └── rbc-ca-bundle.cer          # Your SSL certificate
├── test_web_connectivity.py        # Web access test
├── test_cohere_complete.py         # Complete LLM integration test
├── requirements.txt                # Dependencies
└── README.md                       # This file
```

## Dependencies
- `requests` - HTTP client with SSL support
- `urllib3` - Fallback for SSL certificate issues
- `beautifulsoup4` - Web scraping and content extraction
- `lxml` - XML/HTML parsing
- `openai` - OpenAI client for LLM integration

## Validated Features

✅ **External Web Access**
- Multiple websites accessible
- SSL certificate handling
- Enterprise network compatibility

✅ **LLM Integration** 
- OAuth authentication working
- API connection established
- Streaming responses functional
- Tool calling capabilities confirmed

## Next Steps

With both test components passing, the framework is ready for:
1. Web scraping component development
2. LLM synthesis integration
3. Research report generation
4. Complete web research pipeline

## Troubleshooting

### SSL Issues
- Ensure `rbc-ca-bundle.cer` is in `ssl_certs/` folder
- Check certificate file permissions
- Verify certificate is not expired

### Authentication Issues  
- Update OAuth credentials in CONFIG section
- Verify OAuth endpoint URL is correct
- Check network connectivity to OAuth server

### API Issues
- Confirm base URL endpoint is correct
- Verify OAuth token has proper permissions
- Check API endpoint accessibility from your network