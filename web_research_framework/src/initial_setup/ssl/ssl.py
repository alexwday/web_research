# web_research_framework/src/initial_setup/ssl/ssl.py
"""
SSL Certificate Setup Module

This module handles the SSL certificate setup required for secure web research communication
by configuring environment variables to use an existing certificate. It includes
functionality to validate the certificate's existence and optionally check its
expiration date.

Functions:
    check_certificate_expiry: Validates certificate expiration date
    setup_ssl: Configures SSL environment with existing CA bundle certificate

Dependencies:
    - os
    - logging
    - datetime
    - cryptography (for certificate parsing)
"""

import logging
import os
from datetime import datetime, timedelta, timezone

# Try to import certificate checking libraries, but don't fail if not available in local env
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Import SSL settings
from .ssl_settings import (
    CHECK_CERT_EXPIRY,
    EXPIRY_WARNING_DAYS,
    SSL_CERT_DIR,
    SSL_CERT_FILENAME,
    SSL_CERT_PATH,
)

# Get module logger (no configuration here - using centralized config)
logger = logging.getLogger(__name__)


def check_certificate_expiry(cert_path: str) -> bool:
    """
    Check if the certificate is valid and not expired or expiring soon.

    Args:
        cert_path (str): Path to the certificate file

    Returns:
        bool: True if valid and not expiring soon, False otherwise

    Raises:
        Exception: If there's an error reading or parsing the certificate
    """
    if not CRYPTO_AVAILABLE:
        logger.warning(
            "Cryptography library not available, skipping certificate expiry check"
        )
        return True

    try:
        logger.info(f"Checking certificate expiry for: {cert_path}")

        # Read certificate data
        with open(cert_path, "rb") as cert_file:
            cert_data = cert_file.read()

        # Parse the certificate
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Get expiration date using the UTC method to avoid deprecation warning
        expiry_date = cert.not_valid_after_utc

        # Use timezone-aware current date to match expiry_date's timezone awareness
        current_date = datetime.now(timezone.utc)

        # Check if expired
        if current_date > expiry_date:
            logger.error(f"Certificate expired on {expiry_date.strftime('%Y-%m-%d')}")
            return False

        # Check if expiring soon
        days_until_expiry = (expiry_date - current_date).days
        if days_until_expiry <= EXPIRY_WARNING_DAYS:
            logger.warning(
                f"Certificate will expire in {days_until_expiry} days "
                f"(on {expiry_date.strftime('%Y-%m-%d')})"
            )
            return True

        logger.info(f"Certificate valid until {expiry_date.strftime('%Y-%m-%d')}")
        return True

    except Exception as e:
        logger.error(f"Error checking certificate expiry: {str(e)}")
        raise


def setup_ssl() -> str:
    """
    Configure SSL environment with existing CA bundle certificate.

    This function performs the following steps:
    1. Checks if SSL certificate path is configured (not placeholder)
    2. If using placeholder values, returns a message about local environment
    3. In enterprise environment:
       a. Verifies the certificate file exists
       b. Optionally checks certificate expiration (if enabled in settings)
       c. Sets appropriate environment variables to use the certificate

    Returns:
        str: Path to the configured SSL certificate or placeholder message

    Raises:
        FileNotFoundError: If certificate file does not exist
        Exception: If certificate validation fails
    """
    # Check if we're using placeholder/default values
    if SSL_CERT_DIR == "/path/to/certificates" or SSL_CERT_PATH == "/path/to/certificates/ca-bundle.pem":
        logger.info("SSL certificate setup skipped - using placeholder configuration for local environment")
        return "SSL certificate not configured - using system defaults"

    # Enterprise Environment: Proceed with SSL certificate setup
    # Log settings being used
    logger.info(f"SSL setup starting with settings from: {__file__}")
    logger.info(f"Using certificate directory: {SSL_CERT_DIR}")
    logger.info(f"Using certificate filename: {SSL_CERT_FILENAME}")
    logger.info(f"Full certificate path: {SSL_CERT_PATH}")

    # Verify the certificate exists
    if not os.path.exists(SSL_CERT_PATH):
        error_msg = f"Certificate not found at {SSL_CERT_PATH}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Certificate file exists at {SSL_CERT_PATH}")

    # Check certificate expiry if enabled
    if CHECK_CERT_EXPIRY:
        try:
            check_certificate_expiry(SSL_CERT_PATH)
        except Exception as e:
            logger.warning(f"Certificate expiry check failed: {str(e)}")
    else:
        logger.info("Certificate expiry check disabled")

    # Configure SSL environment variables
    os.environ["SSL_CERT_FILE"] = SSL_CERT_PATH
    os.environ["REQUESTS_CA_BUNDLE"] = SSL_CERT_PATH

    logger.info(
        f"SSL environment configured successfully. Certificate path: {SSL_CERT_PATH}"
    )
    return SSL_CERT_PATH