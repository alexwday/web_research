# web_research_framework/src/initial_setup/ssl/__init__.py
"""
SSL Certificate Setup Package

This package provides SSL certificate configuration functionality for the web research framework.
"""

from .ssl import setup_ssl, check_certificate_expiry
from .ssl_settings import SSL_CERT_PATH, SSL_CERT_DIR, SSL_CERT_FILENAME

__all__ = [
    'setup_ssl',
    'check_certificate_expiry', 
    'SSL_CERT_PATH',
    'SSL_CERT_DIR',
    'SSL_CERT_FILENAME'
]