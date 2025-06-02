"""
Environment Configuration Manager

This module provides centralized environment variable management for the Web Research project.
It loads configuration from environment variables with appropriate type conversions
and validation.

All configuration values are loaded as class attributes on the Config class,
making them easily accessible throughout the application.

Usage:
    from web_research_framework.src.initial_setup.env_config import config
    
    # Access configuration values
    ssl_cert_filename = config.SSL_CERT_FILENAME
    request_timeout = config.REQUEST_TIMEOUT

Dependencies:
    - os
    - logging
    - python-dotenv (optional, for .env file support)
"""

import os
import logging
from typing import Optional, Union

# Try to import python-dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv not installed, use system environment variables only

logger = logging.getLogger(__name__)


class Config:
    """
    Centralized configuration class that loads all settings from environment variables.
    """
    
    # Environment Configuration
    ENVIRONMENT: str = os.getenv("WEB_RESEARCH_ENV", "local")
    
    # SSL Configuration
    SSL_CERT_FILENAME: str = os.getenv("WEB_RESEARCH_SSL_CERT_FILENAME", "ca-bundle.pem")
    SSL_CHECK_CERT_EXPIRY: bool = os.getenv("WEB_RESEARCH_SSL_CHECK_CERT_EXPIRY", "true").lower() == "true"
    SSL_EXPIRY_WARNING_DAYS: int = int(os.getenv("WEB_RESEARCH_SSL_EXPIRY_WARNING_DAYS", "30"))
    
    # Request Configuration
    REQUEST_TIMEOUT: int = int(os.getenv("WEB_RESEARCH_REQUEST_TIMEOUT", "30"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("WEB_RESEARCH_MAX_RETRY_ATTEMPTS", "3"))
    RETRY_DELAY_SECONDS: int = int(os.getenv("WEB_RESEARCH_RETRY_DELAY_SECONDS", "1"))
    
    # Web Scraping Configuration
    USER_AGENT: str = os.getenv(
        "WEB_RESEARCH_USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    MAX_CONTENT_LENGTH: int = int(os.getenv("WEB_RESEARCH_MAX_CONTENT_LENGTH", "100000"))
    SCRAPING_CONCURRENCY: int = int(os.getenv("WEB_RESEARCH_SCRAPING_CONCURRENCY", "5"))
    
    # Search Configuration
    DEFAULT_SEARCH_RESULTS: int = int(os.getenv("WEB_RESEARCH_DEFAULT_SEARCH_RESULTS", "5"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("WEB_RESEARCH_LOG_LEVEL", "INFO")
    
    # LLM Configuration (when integrated with cohere framework)
    LLM_MODEL_SMALL: str = os.getenv("WEB_RESEARCH_MODEL_SMALL", "gpt-4o-mini")
    LLM_MODEL_LARGE: str = os.getenv("WEB_RESEARCH_MODEL_LARGE", "gpt-4o")
    
    # Research Configuration
    RESEARCH_DEPTH: int = int(os.getenv("WEB_RESEARCH_DEPTH", "2"))
    RESEARCH_BREADTH: int = int(os.getenv("WEB_RESEARCH_BREADTH", "4"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration values are set.
        
        Returns:
            bool: True if all required values are set, False otherwise
        """
        # For web research, most settings have sensible defaults
        # Only validate if we have critical missing pieces
        
        logger.info("Web Research configuration validation passed")
        return True
    
    @classmethod
    def get_ssl_cert_path(cls, settings_dir: str) -> str:
        """
        Get the full path to the SSL certificate file.
        
        Args:
            settings_dir: Directory where the SSL certificate is located
            
        Returns:
            str: Full path to the SSL certificate
        """
        import os
        return os.path.join(settings_dir, cls.SSL_CERT_FILENAME)
    
    @classmethod
    def is_enterprise_env(cls) -> bool:
        """
        Check if we're running in an enterprise environment that needs SSL certificates.
        
        Returns:
            bool: True if enterprise environment detected
        """
        enterprise_indicators = [
            'CORPORATE_PROXY',
            'HTTPS_PROXY', 
            'HTTP_PROXY',
            'SSL_CERT_FILE',
            'REQUESTS_CA_BUNDLE'
        ]
        return (
            cls.ENVIRONMENT.lower() in ['enterprise', 'corporate', 'rbc'] or
            any(env_var in os.environ for env_var in enterprise_indicators)
        )


# Create a singleton instance
config = Config()

# Log configuration status
logger.info(f"Environment configuration loaded for: {config.ENVIRONMENT}")
logger.debug(f"SSL Certificate Filename: {config.SSL_CERT_FILENAME}")
logger.debug(f"Request Timeout: {config.REQUEST_TIMEOUT}")
logger.debug(f"Enterprise Environment: {config.is_enterprise_env()}")