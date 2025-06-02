#!/usr/bin/env python3
"""
Research Assistant Application Launcher

Before running:
1. Update config.py with your OAuth credentials and model settings
2. Ensure ssl_certs/rbc-ca-bundle.cer exists
3. Install dependencies: pip install -r requirements.txt
"""

import os
import sys

# Try to import config
try:
    from config import OAUTH_CONFIG, SSL_CERT_PATH, MODEL_NAME
    
    print("Research Assistant Starting...")
    print("-" * 50)
    
    # Check configuration
    missing_config = []
    if OAUTH_CONFIG['oauth_url'] == 'YOUR_OAUTH_URL_HERE':
        missing_config.append("OAuth URL")
    if OAUTH_CONFIG['client_id'] == 'YOUR_CLIENT_ID_HERE':
        missing_config.append("Client ID")
    if OAUTH_CONFIG['client_secret'] == 'YOUR_CLIENT_SECRET_HERE':
        missing_config.append("Client Secret")
    if OAUTH_CONFIG['base_url'] == 'YOUR_COHERE_BASE_URL_HERE':
        missing_config.append("Cohere Base URL")
    
    if missing_config:
        print("ERROR: Please update config.py with your credentials:")
        for item in missing_config:
            print(f"  - {item}")
        print("\nEdit config.py and replace the placeholder values with your actual credentials.")
        print("-" * 50)
        sys.exit(1)
    
    print(f"Configuration loaded successfully")
    print(f"Model: {MODEL_NAME}")
    print("-" * 50)
    
except ImportError:
    print("ERROR: config.py not found")
    print("Please check that config.py exists in the current directory")
    sys.exit(1)

# Check SSL certificate
if not os.path.exists('ssl_certs/rbc-ca-bundle.cer'):
    print("ERROR: SSL certificate not found at ssl_certs/rbc-ca-bundle.cer")
    sys.exit(1)

# Launch the app
print("\nStarting server on http://localhost:8000")
print("Press Ctrl+C to stop")
print("-" * 50)

import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)