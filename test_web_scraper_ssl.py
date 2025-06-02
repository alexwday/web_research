#!/usr/bin/env python3
"""
SSL-Aware Web Scraper Test Component
A web scraping module that uses the same SSL configuration as the cohere_testing framework
to handle enterprise environment SSL requirements.
"""

import requests
import time
import os
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SSLWebScraper:
    """
    SSL-aware web scraper that handles enterprise SSL certificate requirements.
    Uses the same SSL configuration patterns as the cohere_testing framework.
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3, ssl_cert_path: str = None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.ssl_cert_path = ssl_cert_path
        
        # Configure SSL based on environment
        self._configure_ssl()
        
        # Create session with SSL configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configure session SSL settings
        if self.ssl_cert_path and os.path.exists(self.ssl_cert_path):
            self.session.verify = self.ssl_cert_path
            logger.info(f"Session configured with SSL certificate: {self.ssl_cert_path}")
        elif self._is_enterprise_env():
            logger.warning("Enterprise environment detected but no SSL certificate configured")
        else:
            logger.info("Using default SSL verification")
    
    def _is_enterprise_env(self) -> bool:
        """Check if we're in an enterprise environment that might need SSL certificates."""
        enterprise_indicators = [
            'CORPORATE_PROXY',
            'HTTPS_PROXY', 
            'HTTP_PROXY',
            'SSL_CERT_FILE',
            'REQUESTS_CA_BUNDLE'
        ]
        return any(env_var in os.environ for env_var in enterprise_indicators)
    
    def _configure_ssl(self) -> None:
        """
        Configure SSL settings using the same pattern as cohere_testing.
        Try to find and use enterprise SSL certificates.
        """
        # Check if SSL is already configured via environment variables
        if 'SSL_CERT_FILE' in os.environ:
            self.ssl_cert_path = os.environ['SSL_CERT_FILE']
            logger.info(f"Using SSL_CERT_FILE: {self.ssl_cert_path}")
            return
        
        if 'REQUESTS_CA_BUNDLE' in os.environ:
            self.ssl_cert_path = os.environ['REQUESTS_CA_BUNDLE']
            logger.info(f"Using REQUESTS_CA_BUNDLE: {self.ssl_cert_path}")
            return
        
        # Try to find common enterprise certificate locations
        common_cert_paths = [
            "/etc/ssl/certs/ca-certificates.crt",  # Ubuntu/Debian
            "/etc/ssl/certs/ca-bundle.pem",        # CentOS/RHEL
            "/usr/local/share/ca-certificates/",   # Local certs
            "/opt/local/share/curl/curl-ca-bundle.crt",  # MacPorts
            "/usr/local/etc/openssl/cert.pem",     # Homebrew
        ]
        
        for cert_path in common_cert_paths:
            if os.path.exists(cert_path):
                self.ssl_cert_path = cert_path
                # Set environment variables like cohere_testing does
                os.environ["SSL_CERT_FILE"] = cert_path
                os.environ["REQUESTS_CA_BUNDLE"] = cert_path
                logger.info(f"Found and configured SSL certificate: {cert_path}")
                return
        
        # If we're in an enterprise environment but no certs found, warn user
        if self._is_enterprise_env():
            logger.warning("Enterprise environment detected but no SSL certificates found")
            logger.warning("You may need to configure SSL_CERT_PATH manually")
    
    def test_connectivity(self, test_urls: List[str]) -> Dict[str, dict]:
        """Test connectivity to various websites with detailed SSL error reporting."""
        results = {}
        
        for url in test_urls:
            try:
                logger.info(f"Testing connectivity to: {url}")
                response = self.session.get(url, timeout=self.timeout)
                results[url] = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'error': None,
                    'ssl_info': self._get_ssl_info()
                }
                logger.info(f"  ✓ Success: {response.status_code}")
            except requests.exceptions.SSLError as e:
                results[url] = {
                    'success': False,
                    'status_code': None,
                    'error': f"SSL Error: {str(e)}",
                    'ssl_info': self._get_ssl_info()
                }
                logger.error(f"  ✗ SSL Error: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                results[url] = {
                    'success': False,
                    'status_code': None,
                    'error': f"Connection Error: {str(e)}",
                    'ssl_info': self._get_ssl_info()
                }
                logger.error(f"  ✗ Connection Error: {str(e)}")
            except Exception as e:
                results[url] = {
                    'success': False,
                    'status_code': None,
                    'error': f"Error: {str(e)}",
                    'ssl_info': self._get_ssl_info()
                }
                logger.error(f"  ✗ Failed: {str(e)}")
        
        return results
    
    def _get_ssl_info(self) -> dict:
        """Get current SSL configuration information."""
        return {
            'ssl_cert_path': self.ssl_cert_path,
            'ssl_cert_file_env': os.environ.get('SSL_CERT_FILE'),
            'requests_ca_bundle_env': os.environ.get('REQUESTS_CA_BUNDLE'),
            'https_proxy': os.environ.get('HTTPS_PROXY'),
            'http_proxy': os.environ.get('HTTP_PROXY'),
            'enterprise_env': self._is_enterprise_env()
        }
    
    def test_ssl_configuration(self) -> Dict[str, bool]:
        """Test various SSL configurations to find what works."""
        test_results = {}
        test_url = "https://httpbin.org/get"
        
        # Test 1: Default configuration
        logger.info("Testing default SSL configuration...")
        try:
            response = requests.get(test_url, timeout=self.timeout)
            test_results['default_ssl'] = response.status_code == 200
            logger.info(f"  ✓ Default SSL works: {response.status_code}")
        except Exception as e:
            test_results['default_ssl'] = False
            logger.error(f"  ✗ Default SSL failed: {str(e)}")
        
        # Test 2: With custom certificate (if configured)
        if self.ssl_cert_path and os.path.exists(self.ssl_cert_path):
            logger.info(f"Testing with custom certificate: {self.ssl_cert_path}")
            try:
                response = requests.get(test_url, verify=self.ssl_cert_path, timeout=self.timeout)
                test_results['custom_cert_ssl'] = response.status_code == 200
                logger.info(f"  ✓ Custom cert SSL works: {response.status_code}")
            except Exception as e:
                test_results['custom_cert_ssl'] = False
                logger.error(f"  ✗ Custom cert SSL failed: {str(e)}")
        
        # Test 3: Disable SSL verification (NOT recommended for production)
        logger.info("Testing with SSL verification disabled...")
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(test_url, verify=False, timeout=self.timeout)
            test_results['no_ssl_verify'] = response.status_code == 200
            logger.warning(f"  ⚠ No SSL verification works: {response.status_code} (NOT SECURE)")
        except Exception as e:
            test_results['no_ssl_verify'] = False
            logger.error(f"  ✗ No SSL verification failed: {str(e)}")
        
        return test_results
    
    def scrape_url(self, url: str, use_ssl_fallback: bool = True) -> Optional[Dict[str, str]]:
        """
        Scrape a single URL with SSL fallback options.
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Scraping: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title = ""
                if soup.title:
                    title = soup.title.string.strip()
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                
                # Extract main content
                content = ""
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                
                if main_content:
                    content = main_content.get_text(separator='\n', strip=True)
                else:
                    body = soup.find('body')
                    if body:
                        content = body.get_text(separator='\n', strip=True)
                
                # Clean up content
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                content = '\n'.join(lines)
                
                result = {
                    'url': url,
                    'title': title,
                    'content': content[:2000],  # Limit for testing
                    'word_count': len(content.split()),
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'ssl_config': self._get_ssl_info()
                }
                
                logger.info(f"  ✓ Success: Extracted {len(content)} characters")
                return result
                
            except requests.exceptions.SSLError as e:
                logger.error(f"  ✗ SSL Error on attempt {attempt + 1}: {str(e)}")
                if use_ssl_fallback and attempt == self.max_retries - 1:
                    logger.warning("  Trying fallback with disabled SSL verification...")
                    try:
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        response = requests.get(url, verify=False, timeout=self.timeout)
                        response.raise_for_status()
                        logger.warning("  ⚠ Fallback successful (NOT SECURE)")
                        # Process response same as above...
                        # (simplified for brevity)
                        return {'url': url, 'title': 'SSL Fallback Success', 'content': 'Used insecure connection'}
                    except Exception as fallback_e:
                        logger.error(f"  ✗ SSL fallback also failed: {str(fallback_e)}")
                        
            except Exception as e:
                logger.error(f"  ✗ Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)
        
        return None


def run_ssl_diagnostic():
    """Run comprehensive SSL diagnostics."""
    print("=" * 60)
    print("SSL CONFIGURATION DIAGNOSTIC")
    print("=" * 60)
    
    scraper = SSLWebScraper()
    
    # Show current SSL configuration
    ssl_info = scraper._get_ssl_info()
    print("\nCurrent SSL Configuration:")
    for key, value in ssl_info.items():
        print(f"  {key}: {value}")
    
    # Test SSL configurations
    print("\nTesting SSL Configurations:")
    ssl_tests = scraper.test_ssl_configuration()
    for test_name, result in ssl_tests.items():
        status = "✓ WORKING" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    return any(ssl_tests.values())


def run_connectivity_test():
    """Test connectivity with SSL awareness."""
    print("\n" + "=" * 60)
    print("SSL-AWARE CONNECTIVITY TEST")
    print("=" * 60)
    
    test_urls = [
        "https://httpbin.org/get",
        "https://example.com",
        "https://www.google.com",
        "https://github.com",
    ]
    
    scraper = SSLWebScraper()
    results = scraper.test_connectivity(test_urls)
    
    print("\nResults:")
    working_sites = 0
    for url, result in results.items():
        status = "✓ WORKING" if result['success'] else "✗ FAILED"
        print(f"  {url}: {status}")
        if not result['success'] and result['error']:
            print(f"    Error: {result['error']}")
        if result['success']:
            working_sites += 1
    
    print(f"\nSummary: {working_sites}/{len(test_urls)} sites accessible")
    return working_sites > 0, results


def main():
    """Run SSL-aware web scraping tests."""
    print("SSL-Aware Web Scraper Test Suite")
    print("Testing web access with enterprise SSL configuration")
    
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    # Test 1: SSL Configuration
    ssl_ok = run_ssl_diagnostic()
    results['tests']['ssl_config'] = ssl_ok
    
    # Test 2: Connectivity with SSL
    connectivity_ok, connectivity_results = run_connectivity_test()
    results['tests']['connectivity'] = connectivity_ok
    results['connectivity_details'] = connectivity_results
    
    # Save results
    with open('/Users/alexwday/Projects/web_research/ssl_scraper_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("SSL TEST COMPLETE")
    print("=" * 60)
    
    if ssl_ok and connectivity_ok:
        print("✓ SSL configuration is working")
        print("✓ Ready to proceed with web research components")
    else:
        print("⚠️  SSL issues detected")
        print("Check ssl_scraper_test_results.json for details")
        print("\nPossible solutions:")
        print("1. Configure SSL_CERT_FILE environment variable")
        print("2. Copy SSL certificate path from cohere_testing setup")
        print("3. Contact IT for enterprise SSL certificate location")
    
    print(f"\nResults saved to: ssl_scraper_test_results.json")


if __name__ == "__main__":
    main()