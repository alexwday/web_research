#!/usr/bin/env python3
"""
Research Assistant Application Launcher

Before running:
1. Update CONFIG in app.py with your OAuth credentials
2. Ensure ssl_certs/rbc-ca-bundle.cer exists
3. Install dependencies: pip install -r requirements.txt
"""

import os
import sys

# Check for required environment variables or config
required_config = {
    'OAUTH_URL': 'OAuth token endpoint URL',
    'OAUTH_CLIENT_ID': 'OAuth client ID',
    'OAUTH_CLIENT_SECRET': 'OAuth client secret',
    'COHERE_BASE_URL': 'Cohere API base URL'
}

print("Research Assistant Starting...")
print("-" * 50)

# Check configuration
missing_config = []
for key, desc in required_config.items():
    if not os.getenv(key):
        missing_config.append(f"{key}: {desc}")

if missing_config:
    print("WARNING: Missing configuration:")
    for item in missing_config:
        print(f"  - {item}")
    print("\nYou can either:")
    print("1. Set these as environment variables")
    print("2. Update CONFIG dict in app.py directly")
    print("-" * 50)

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