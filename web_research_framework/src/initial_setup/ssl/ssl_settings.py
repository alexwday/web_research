# web_research_framework/src/initial_setup/ssl/ssl_settings.py
"""
SSL Certificate Settings Configuration

This module defines the configuration settings for SSL certificates used in web research API communication.

Attributes:
    SSL_CERT_DIR (str): Directory where SSL certificates are stored
    SSL_CERT_FILENAME (str): Filename of the SSL certificate
    SSL_CERT_PATH (str): Full path to the SSL certificate
    CHECK_CERT_EXPIRY (bool): Whether to check certificate expiration
    EXPIRY_WARNING_DAYS (int): Number of days before expiry to start warning

Dependencies:
    - os
    - logging
"""

import os
import logging

# Get module logger (no configuration here - using centralized config)
logger = logging.getLogger(__name__)

# Certificate location
SSL_CERT_DIR = "/path/to/certificates"  # Replace with actual certificate directory in production
SSL_CERT_FILENAME = "ca-bundle.pem"  # Replace with actual certificate filename in production
SSL_CERT_PATH = os.path.join(SSL_CERT_DIR, SSL_CERT_FILENAME)

# Certificate validation settings
CHECK_CERT_EXPIRY = True  # Whether to check certificate expiration
EXPIRY_WARNING_DAYS = 30  # Start warning this many days before expiry

logger.debug("SSL settings initialized")