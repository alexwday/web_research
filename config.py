"""
Configuration file for Research Assistant
Update these values with your actual credentials
"""

# OAuth Configuration
OAUTH_CONFIG = {
    'oauth_url': 'YOUR_OAUTH_URL_HERE',  # e.g., 'https://auth.example.com/oauth/token'
    'client_id': 'YOUR_CLIENT_ID_HERE',
    'client_secret': 'YOUR_CLIENT_SECRET_HERE',
    'base_url': 'YOUR_COHERE_BASE_URL_HERE'  # e.g., 'https://api.example.com/v1'
}

# SSL Certificate Path
SSL_CERT_PATH = 'ssl_certs/rbc-ca-bundle.cer'

# Model Configuration
MODEL_NAME = 'gpt-4o-mini-2024-07-18'  # or 'gpt-4o-2024-05-13'
MAX_TOKENS = 4096  # Maximum tokens for model responses

# Server Configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# WebSocket Configuration
WS_RECONNECT_INTERVAL = 3000  # milliseconds

# Research Configuration
MAX_SEARCH_RESULTS = 5
MAX_CONTENT_LENGTH = 3000
REQUEST_TIMEOUT = 10  # seconds