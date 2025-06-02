# SSL Configuration for Web Research Framework

## Overview

The web research framework includes its own SSL configuration module that follows the same pattern as the iris-project framework. The SSL certificate is automatically detected from the framework's SSL directory.

## Configuration

### For Enterprise/Work Environments

1. **Get your SSL certificate file** from your IT department
   - Usually named something like `ca-bundle.pem`, `company-cert.pem`, etc.

2. **Place the certificate in the SSL directory**:
   ```bash
   cp /path/to/your/certificate.pem web_research_framework/src/initial_setup/ssl/ca-bundle.pem
   ```

3. **The framework will automatically**:
   - Detect the certificate file in its SSL directory
   - Set `SSL_CERT_FILE` environment variable
   - Set `REQUESTS_CA_BUNDLE` environment variable
   - Validate certificate expiration (optional)

### For Local Development

The framework works out of the box with system SSL certificates. If no certificate file is found in the SSL directory, it uses system defaults.

## Testing SSL Configuration

Run the SSL-aware test:

```bash
python test_web_scraper_ssl.py
```

This will:
- Test SSL configuration
- Verify connectivity to test sites
- Provide detailed error reporting
- Save results to `ssl_scraper_test_results.json`

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

The framework also respects these standard SSL environment variables:
- `SSL_CERT_FILE` - Set automatically by the framework
- `REQUESTS_CA_BUNDLE` - Set automatically by the framework
- `HTTPS_PROXY` - HTTPS proxy server
- `HTTP_PROXY` - HTTP proxy server

## Troubleshooting

### SSL Certificate Errors

1. **"Certificate not found"**: Place certificate in `web_research_framework/src/initial_setup/ssl/` directory
2. **"SSL verification failed"**: Contact IT for correct certificate
3. **"Certificate expired"**: Request updated certificate from IT

### Testing Commands

```bash
# Test basic connectivity
python -c "import requests; print(requests.get('https://httpbin.org/get').status_code)"

# Test SSL setup
python -c "from web_research_framework.src.initial_setup.ssl import setup_ssl; print(setup_ssl())"

# Test with custom certificate name
WEB_RESEARCH_SSL_CERT_FILENAME="my-cert.pem" python test_web_scraper_ssl.py
```

## Certificate File Location

The SSL certificate should be placed here:
```
web_research_framework/src/initial_setup/ssl/ca-bundle.pem
```

The framework automatically looks for the certificate in this location and configures SSL accordingly.

## Integration with Existing Systems

The SSL module can be imported and used in other components:

```python
from web_research_framework.src.initial_setup.ssl import setup_ssl

# Configure SSL for the current session
ssl_cert_path = setup_ssl()
```

This ensures consistent SSL handling across all web research components.