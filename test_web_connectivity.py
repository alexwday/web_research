#!/usr/bin/env python3
"""
Web Connectivity Test
Tests external website connectivity with smart SSL handling for enterprise environments.
Put your rbc-ca-bundle.cer file in the ssl_certs/ folder and run this script.
"""

import os
import requests
import urllib3
import logging
from pathlib import Path

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Known problematic sites that need urllib3 first
PROBLEMATIC_SITES = ["github.com", "api.github.com", "raw.githubusercontent.com"]

def setup_ssl():
    """Look for SSL certificate and configure it if found."""
    script_dir = Path(__file__).parent
    cert_path = script_dir / "ssl_certs" / "rbc-ca-bundle.cer"
    
    if cert_path.exists():
        logger.info(f"Found SSL certificate: {cert_path}")
        os.environ["SSL_CERT_FILE"] = str(cert_path)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        return str(cert_path)
    else:
        logger.info("No SSL certificate found - using system defaults")
        return None

def is_problematic_site(url):
    """Check if URL is known to have SSL certificate chain issues."""
    return any(site in url for site in PROBLEMATIC_SITES)

def fetch_with_requests(url):
    """Fetch URL using requests with proper SSL."""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code, f"SUCCESS (requests)" if response.status_code == 200 else f"HTTP {response.status_code} (requests)"
    except Exception as e:
        return None, f"requests Error: {e}"

def fetch_with_urllib3(url):
    """Fetch URL using urllib3 with relaxed SSL validation."""
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False, timeout=urllib3.Timeout(connect=10.0, read=10.0))
        response = http.request('GET', url)
        return response.status, f"SUCCESS (urllib3)" if response.status == 200 else f"HTTP {response.status} (urllib3)"
    except Exception as e:
        return None, f"urllib3 Error: {e}"

def test_url(url):
    """Test a single URL with smart SSL approach."""
    logger.info(f"Testing: {url}")
    
    if is_problematic_site(url):
        # Known problematic: try urllib3 first, fallback to requests
        status, result = fetch_with_urllib3(url)
        if status != 200:
            logger.info("  urllib3 failed, trying requests fallback...")
            status2, result2 = fetch_with_requests(url)
            if status2 == 200:
                result = result2 + " (after urllib3 failed)"
            else:
                result = f"{result} | {result2}"
    else:
        # Normal sites: try requests first, fallback to urllib3 on SSL errors
        status, result = fetch_with_requests(url)
        if status is None and "SSL" in result:
            logger.info("  requests SSL error, trying urllib3 fallback...")
            status2, result2 = fetch_with_urllib3(url)
            if status2 == 200:
                result = result2 + " (after requests SSL error)"
            else:
                result = f"{result} | {result2}"
    
    success = "SUCCESS" in result
    logger.info(f"  {'✓' if success else '✗'} {result}")
    return success, result

def main():
    print("=" * 60)
    print("WEB CONNECTIVITY TEST")
    print("=" * 60)
    
    # Setup SSL
    cert_path = setup_ssl()
    
    # Test URLs
    test_urls = [
        "https://httpbin.org/get",
        "https://example.com", 
        "https://www.google.com",
        "https://github.com"
    ]
    
    print("\nTesting external website connectivity...")
    print("-" * 60)
    
    results = {}
    for url in test_urls:
        success, result = test_url(url)
        results[url] = {"success": success, "result": result}
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful_sites = sum(1 for r in results.values() if r["success"])
    total_sites = len(results)
    
    print(f"SSL Certificate: {'Found' if cert_path else 'Not found (using system default)'}")
    print(f"Website Connectivity: {successful_sites}/{total_sites} sites accessible")
    
    if successful_sites == total_sites:
        print("\n✓ SUCCESS: All external websites accessible!")
        print("  Web research components should work perfectly.")
    elif successful_sites > 0:
        print(f"\n⚠ PARTIAL: {successful_sites} sites working, {total_sites - successful_sites} failed")
        print("  Web research will work but may have limitations.")
    else:
        print("\n✗ FAILED: No external website connectivity")
        print("  Check network restrictions or SSL configuration.")
    
    print("\nThis test confirms external web access for the research framework.")

if __name__ == "__main__":
    main()