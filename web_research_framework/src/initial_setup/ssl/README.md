# SSL Certificate Setup

## Overview

This directory contains SSL certificate configuration for the web research framework. The SSL module automatically looks for certificate files in this directory.

## Certificate Placement

To use enterprise SSL certificates:

1. **Place your certificate file in this directory**:
   ```
   web_research_framework/src/initial_setup/ssl/ca-bundle.pem
   ```

2. **The certificate file should be named**: `ca-bundle.pem` (default)
   - Or set `WEB_RESEARCH_SSL_CERT_FILENAME` environment variable to use a different name

3. **The framework will automatically**:
   - Detect the certificate file
   - Configure `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` environment variables
   - Validate certificate expiration (if enabled)

## Environment Variables

Configure SSL behavior with these environment variables:

```bash
# Certificate filename (default: ca-bundle.pem)
export WEB_RESEARCH_SSL_CERT_FILENAME="your-cert.pem"

# Enable/disable certificate expiration checking (default: true)
export WEB_RESEARCH_SSL_CHECK_CERT_EXPIRY="true"

# Days before expiry to start warning (default: 30)
export WEB_RESEARCH_SSL_EXPIRY_WARNING_DAYS="30"
```

## For Enterprise/Work Environments

1. **Get your SSL certificate from IT department**
2. **Copy it to this directory**:
   ```bash
   cp /path/to/your/enterprise-cert.pem web_research_framework/src/initial_setup/ssl/ca-bundle.pem
   ```
3. **Test the configuration**:
   ```bash
   python test_web_scraper_ssl.py
   ```

## For Local Development

If no certificate file is found in this directory, the framework will:
- Use system default SSL certificates
- Log a message about using system defaults
- Continue operation normally

## File Structure

```
ssl/
├── README.md           # This file
├── __init__.py         # Package initialization
├── ssl.py             # SSL setup logic
└── ca-bundle.pem      # Your SSL certificate (place here)
```

## Troubleshooting

### Certificate Not Found
- Ensure certificate file is in this directory
- Check filename matches `WEB_RESEARCH_SSL_CERT_FILENAME`
- Verify file permissions

### SSL Verification Errors
- Confirm certificate is valid and not expired
- Contact IT for updated certificate
- Check certificate format (should be PEM format)

### Testing SSL Configuration
```bash
# Test with environment variable
WEB_RESEARCH_SSL_CERT_FILENAME="my-cert.pem" python test_web_scraper_ssl.py

# Test basic SSL
python -c "from web_research_framework.src.initial_setup.ssl import setup_ssl; print(setup_ssl())"
```