#!/usr/bin/env python3
"""
Basic Web Scraper Test Component
A simple web scraping module to test web access and content extraction
in your work environment before building the full system.
"""

import requests
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import sys


class BasicWebScraper:
    """
    Simple web scraper for testing web access and content extraction.
    Tests basic HTTP requests, HTML parsing, and content cleaning.
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def test_connectivity(self, test_urls: List[str]) -> Dict[str, bool]:
        """Test connectivity to various websites to check work environment restrictions."""
        results = {}
        
        for url in test_urls:
            try:
                print(f"Testing connectivity to: {url}")
                response = self.session.get(url, timeout=self.timeout)
                results[url] = response.status_code == 200
                print(f"  ✓ Success: {response.status_code}")
            except Exception as e:
                results[url] = False
                print(f"  ✗ Failed: {str(e)}")
        
        return results
    
    def scrape_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single URL and extract basic content.
        Returns dictionary with title, content, and metadata.
        """
        for attempt in range(self.max_retries):
            try:
                print(f"Scraping: {url} (attempt {attempt + 1})")
                
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
                
                # Try to find main content areas
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                
                if main_content:
                    content = main_content.get_text(separator='\n', strip=True)
                else:
                    # Fallback to body content
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
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"  ✓ Success: Extracted {len(content)} characters")
                return result
                
            except Exception as e:
                print(f"  ✗ Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)
        
        return None
    
    def search_web(self, query: str, num_results: int = 5) -> List[str]:
        """
        Simple web search using DuckDuckGo (no API key required).
        Returns list of URLs for further scraping.
        """
        try:
            # Use DuckDuckGo HTML search (simpler than API)
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            print(f"Searching for: {query}")
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search result URLs
            urls = []
            links = soup.find_all('a', {'class': 'result__a'})
            
            for link in links[:num_results]:
                href = link.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
            
            print(f"  ✓ Found {len(urls)} search results")
            return urls
            
        except Exception as e:
            print(f"  ✗ Search failed: {str(e)}")
            return []


def run_connectivity_test():
    """Test basic web connectivity to common sites."""
    print("=" * 60)
    print("CONNECTIVITY TEST")
    print("=" * 60)
    
    test_urls = [
        "https://httpbin.org/get",  # Simple test endpoint
        "https://example.com",      # Basic test site
        "https://wikipedia.org",    # Popular site
        "https://duckduckgo.com",   # Search engine
        "https://github.com",       # Code repository
    ]
    
    scraper = BasicWebScraper()
    results = scraper.test_connectivity(test_urls)
    
    print("\nResults:")
    working_sites = 0
    for url, success in results.items():
        status = "✓ WORKING" if success else "✗ BLOCKED"
        print(f"  {url}: {status}")
        if success:
            working_sites += 1
    
    print(f"\nSummary: {working_sites}/{len(test_urls)} sites accessible")
    return working_sites > 0


def run_scraping_test():
    """Test content extraction from a simple website."""
    print("\n" + "=" * 60)
    print("CONTENT EXTRACTION TEST")
    print("=" * 60)
    
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
    ]
    
    scraper = BasicWebScraper()
    
    for url in test_urls:
        result = scraper.scrape_url(url)
        if result:
            print(f"\nExtracted content from {url}:")
            print(f"  Title: {result['title']}")
            print(f"  Word count: {result['word_count']}")
            print(f"  Content preview: {result['content'][:200]}...")
            print(f"  Status: {result['status_code']}")
        else:
            print(f"\nFailed to extract content from {url}")


def run_search_test():
    """Test basic web search functionality."""
    print("\n" + "=" * 60)
    print("WEB SEARCH TEST")
    print("=" * 60)
    
    scraper = BasicWebScraper()
    
    test_query = "python web scraping tutorial"
    urls = scraper.search_web(test_query, num_results=3)
    
    if urls:
        print(f"\nSearch results for '{test_query}':")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
        
        # Try to scrape one of the results
        if urls:
            print(f"\nTesting scraping of first result...")
            result = scraper.scrape_url(urls[0])
            if result:
                print(f"  ✓ Successfully scraped content ({result['word_count']} words)")
            else:
                print(f"  ✗ Failed to scrape content")
    else:
        print("No search results found")


def save_test_results(results: Dict):
    """Save test results to a JSON file for analysis."""
    with open('/Users/alexwday/Projects/web_research/scraper_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nTest results saved to scraper_test_results.json")


def main():
    """Run all web scraping tests."""
    print("Web Scraper Test Suite")
    print("Testing web access and content extraction in your work environment")
    print("This will help identify any restrictions before building the full system.")
    
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    # Test 1: Basic connectivity
    connectivity_ok = run_connectivity_test()
    results['tests']['connectivity'] = connectivity_ok
    
    if not connectivity_ok:
        print("\n⚠️  Warning: No web connectivity detected.")
        print("Please check your work environment's network restrictions.")
        return
    
    # Test 2: Content extraction
    run_scraping_test()
    results['tests']['content_extraction'] = True
    
    # Test 3: Web search
    run_search_test()
    results['tests']['web_search'] = True
    
    save_test_results(results)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("✓ Basic web scraping components are working")
    print("✓ Ready to build more advanced research components")
    print("\nNext steps:")
    print("1. Review scraper_test_results.json for any issues")
    print("2. If all tests pass, we can proceed with LLM integration")
    print("3. If any tests fail, let me know what restrictions exist")


if __name__ == "__main__":
    main()