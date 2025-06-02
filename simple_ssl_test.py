#!/usr/bin/env python3
"""
Simple SSL Web Test
Just tests if web scraping works with your SSL certificate.
Put your rbc-ca-bundle.cer file in the ssl_certs/ folder and run this script.
"""

import os
import requests
import logging
from pathlib import Path

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def setup_ssl():
    """Look for SSL certificate and configure it if found."""
    # Look for the certificate file
    script_dir = Path(__file__).parent
    cert_path = script_dir / "ssl_certs" / "rbc-ca-bundle.cer"
    
    if cert_path.exists():
        logger.info(f"Found SSL certificate: {cert_path}")
        # Set environment variables like iris-project does
        os.environ["SSL_CERT_FILE"] = str(cert_path)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        return str(cert_path)
    else:
        logger.info(f"No SSL certificate found at {cert_path}")
        logger.info("Using system default SSL certificates")
        return None

def test_websites():
    """Test connectivity to various websites."""
    test_urls = [
        "https://httpbin.org/get",
        "https://example.com", 
        "https://www.google.com",
        "https://github.com"
    ]
    
    results = {}
    
    for url in test_urls:
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
            logger.error(f"  ✗ SSL ERROR: {e}")
            results[url] = f"SSL Error: {e}"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"  ✗ CONNECTION ERROR: {e}")
            results[url] = f"Connection Error: {e}"
        except Exception as e:
            logger.error(f"  ✗ ERROR: {e}")
            results[url] = f"Error: {e}"
    
    return results

def test_basic_scraping():
    """Test basic web scraping."""
    test_url = "https://httpbin.org/html"
    
    try:
        logger.info(f"Testing web scraping: {test_url}")
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        
        # Simple content check
        content = response.text
        if "Herman Melville" in content:  # httpbin.org/html contains this
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
    print("SIMPLE SSL WEB TEST")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Put your rbc-ca-bundle.cer file in the ssl_certs/ folder")
    print("2. Run this script: python simple_ssl_test.py")
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
    
    successful_sites = sum(1 for result in results.values() if result == "SUCCESS")
    total_sites = len(results)
    
    print(f"SSL Certificate: {'Found' if cert_path else 'Not found (using system default)'}")
    print(f"Website Connectivity: {successful_sites}/{total_sites} sites accessible")
    print(f"Web Scraping: {'Working' if scraping_works else 'Failed'}")
    
    if successful_sites > 0 and scraping_works:
        print()
        print("✓ SUCCESS: Web research components should work in your environment!")
    elif successful_sites > 0:
        print()
        print("⚠ PARTIAL: Basic connectivity works but scraping has issues")
    else:
        print()
        print("✗ FAILED: No web connectivity - check SSL certificate or network restrictions")
        
        if not cert_path:
            print()
            print("Next steps:")
            print("1. Get rbc-ca-bundle.cer from IT or copy from iris-project")
            print("2. Place it in ssl_certs/rbc-ca-bundle.cer")
            print("3. Run this test again")

if __name__ == "__main__":
    main()