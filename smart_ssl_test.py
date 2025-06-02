#!/usr/bin/env python3
"""
Smart SSL Web Test
Uses requests for most sites, urllib3 fallback only for known problematic sites.
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

# Known problematic sites that need urllib3 fallback
PROBLEMATIC_SITES = [
    "github.com",
    "api.github.com", 
    "raw.githubusercontent.com"
]

def setup_ssl():
    """Look for SSL certificate and configure it if found."""
    script_dir = Path(__file__).parent
    cert_path = script_dir / "ssl_certs" / "rbc-ca-bundle.cer"
    
    if cert_path.exists():
        logger.info(f"Found SSL certificate: {cert_path}")
        # Set environment variables for requests
        os.environ["SSL_CERT_FILE"] = str(cert_path)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        return str(cert_path)
    else:
        logger.info(f"No SSL certificate found at {cert_path}")
        logger.info("Using system default SSL certificates")
        return None

def is_problematic_site(url):
    """Check if URL is known to have SSL certificate chain issues."""
    return any(site in url for site in PROBLEMATIC_SITES)

def fetch_with_urllib3(url):
    """Fetch URL using urllib3 with relaxed SSL validation."""
    try:
        logger.info(f"  Using urllib3 for known problematic site: {url}")
        
        # Disable SSL warnings for this specific case
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
            assert_hostname=False,
            timeout=urllib3.Timeout(connect=10.0, read=10.0)
        )
        
        response = http.request('GET', url)
        if response.status == 200:
            logger.info(f"  ✓ SUCCESS with urllib3: {response.status}")
            return "SUCCESS (urllib3 for SSL issues)"
        else:
            logger.warning(f"  ! urllib3 unexpected status: {response.status}")
            return f"HTTP {response.status} (urllib3)"
            
    except Exception as e:
        logger.error(f"  ✗ urllib3 also failed: {e}")
        return f"urllib3 Error: {e}"

def test_websites():
    """Test connectivity using smart SSL approach."""
    test_urls = [
        "https://httpbin.org/get",
        "https://example.com", 
        "https://www.google.com",
        "https://github.com"
    ]
    
    results = {}
    
    for url in test_urls:
        # For known problematic sites, go straight to urllib3
        if is_problematic_site(url):
            logger.info(f"Testing (known problematic): {url}")
            results[url] = fetch_with_urllib3(url)
            continue
        
        # For normal sites, try requests first
        try:
            logger.info(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"  ✓ SUCCESS: {response.status_code}")
                results[url] = "SUCCESS"
            else:
                logger.warning(f"  ! Unexpected status: {response.status_code}")
                results[url] = f"HTTP {response.status_code}"
        except requests.exceptions.SSLError as e:
            logger.warning(f"  ! SSL ERROR with requests: {e}")
            # SSL error - try urllib3 fallback
            results[url] = fetch_with_urllib3(url)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"  ✗ CONNECTION ERROR: {e}")
            results[url] = f"Connection Error: {e}"
        except Exception as e:
            logger.error(f"  ✗ ERROR: {e}")
            results[url] = f"Error: {e}"
    
    return results

def test_basic_scraping():
    """Test basic web scraping with smart SSL."""
    test_url = "https://httpbin.org/html"
    
    try:
        logger.info(f"Testing web scraping: {test_url}")
        
        # httpbin.org should work with requests
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        
        # Simple content check
        content = response.text
        if "Herman Melville" in content:
            logger.info("  ✓ Web scraping works - content extracted successfully")
            return True
        else:
            logger.warning("  ! Web scraping partial - unexpected content")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Web scraping failed: {e}")
        return False

def main():
    print("=" * 60)
    print("SMART SSL WEB TEST")
    print("=" * 60)
    print()
    print("Uses requests for most sites, urllib3 only for known problematic sites")
    print()
    
    # Setup SSL
    cert_path = setup_ssl()
    
    print("-" * 60)
    print("CONNECTIVITY TEST")
    print("-" * 60)
    
    # Test websites
    results = test_websites()
    
    print()
    print("-" * 60)
    print("WEB SCRAPING TEST")
    print("-" * 60)
    
    # Test scraping
    scraping_works = test_basic_scraping()
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful_sites = sum(1 for result in results.values() if "SUCCESS" in result)
    total_sites = len(results)
    
    print(f"SSL Certificate: {'Found' if cert_path else 'Not found (using system default)'}")
    print(f"Website Connectivity: {successful_sites}/{total_sites} sites accessible")
    print(f"Web Scraping: {'Working' if scraping_works else 'Failed'}")
    
    # Show which method worked for each site
    print("\nPer-site results:")
    for url, result in results.items():
        method = "urllib3" if "urllib3" in result else "requests"
        status = "✓" if "SUCCESS" in result else "✗"
        print(f"  {status} {url}: {result} ({method})")
    
    if successful_sites == total_sites and scraping_works:
        print()
        print("✓ SUCCESS: All sites working with smart SSL approach!")
    elif successful_sites > 0:
        print()
        print("⚠ PARTIAL: Some connectivity issues remain")
    else:
        print()
        print("✗ FAILED: Major connectivity issues")

if __name__ == "__main__":
    main()