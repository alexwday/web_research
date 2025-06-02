# SSL Configuration for Web Research Framework

## Overview

The web research framework includes its own SSL configuration module that follows the same pattern as the cohere_testing framework. This ensures secure web scraping in enterprise environments.

## Configuration

### For Enterprise/Work Environments

1. **Locate your SSL certificate file** (usually provided by IT department)
   - Common locations: `/path/to/company/certificates/ca-bundle.pem`
   - Ask IT for the certificate path

2. **Configure the SSL settings**:
   Edit `web_research_framework/src/initial_setup/ssl/ssl_settings.py`:

   ```python
   # Replace these with your actual certificate paths
   SSL_CERT_DIR = "/path/to/your/certificates"
   SSL_CERT_FILENAME = "your-ca-bundle.pem"  
   ```

3. **The framework will automatically**:
   - Set `SSL_CERT_FILE` environment variable
   - Set `REQUESTS_CA_BUNDLE` environment variable
   - Validate certificate expiration (optional)

### For Local Development

The framework works out of the box with system SSL certificates. No configuration needed.

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

The framework respects these environment variables:

- `SSL_CERT_FILE` - Path to SSL certificate
- `REQUESTS_CA_BUNDLE` - Alternative SSL certificate path
- `HTTPS_PROXY` - HTTPS proxy server
- `HTTP_PROXY` - HTTP proxy server

## Troubleshooting

### SSL Certificate Errors

1. **"Certificate not found"**: Update paths in `ssl_settings.py`
2. **"SSL verification failed"**: Contact IT for correct certificate
3. **"Certificate expired"**: Request updated certificate from IT

### Testing Commands

```bash
# Test basic connectivity
python -c "import requests; print(requests.get('https://httpbin.org/get').status_code)"

# Test with your certificate
SSL_CERT_FILE=/path/to/cert.pem python test_web_scraper_ssl.py
```

## Integration with Existing Systems

The SSL module can be imported and used in other components:

```python
from web_research_framework.src.initial_setup.ssl import setup_ssl

# Configure SSL for the current session
ssl_cert_path = setup_ssl()
```

This ensures consistent SSL handling across all web research components.